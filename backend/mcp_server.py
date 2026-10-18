#!/usr/bin/env python3
"""Local MCP (Model Context Protocol) Server for Remote Job Radar & Application Tracker.

Memungkinkan agen AI (Antigravity, Cursor, Claude Desktop, dsb) untuk berinteraksi langsung
dengan database lowongan lokal, memfilter peluang remote Indonesia, dan mengelola Kanban status via stdio JSON-RPC.
"""

import sys
import json
import logging
from typing import Any, Dict, List, Optional
import os

# Tambahkan path backend
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import (
    get_all_jobs,
    get_connection,
    upsert_application,
    get_all_tracked_applications,
)

logging.basicConfig(level=logging.ERROR, stream=sys.stderr)


# Definisi Tools MCP
TOOLS = [
    {
        "name": "get_verified_remote_jobs",
        "description": "Mengambil daftar lowongan remote terverifikasi yang secara eksplisit menerima pelamar dari Indonesia.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Jumlah maksimal lowongan yang diambil (default: 10)",
                    "default": 10
                },
                "only_small_companies": {
                    "type": "boolean",
                    "description": "Hanya tampilkan perusahaan kecil (10-100 karyawan)",
                    "default": True
                }
            }
        }
    },
    {
        "name": "search_remote_jobs",
        "description": "Mencari lowongan kerja remote berdasarkan kata kunci (contoh: 'python', 'laravel', 'vue', 'ai engineer').",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Kata kunci pencarian judul atau keahlian"
                },
                "min_fit_score": {
                    "type": "integer",
                    "description": "Skor kecocokan minimal 0-100 (default: 0)",
                    "default": 0
                },
                "limit": {
                    "type": "integer",
                    "description": "Jumlah maksimal hasil (default: 10)",
                    "default": 10
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "get_job_details",
        "description": "Mengambil detail lengkap lowongan termasuk bukti kutipan verbatim kelayakan domisili Indonesia dan analisis fit.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "job_id": {
                    "type": "string",
                    "description": "ID unik lowongan kerja"
                }
            },
            "required": ["job_id"]
        }
    },
    {
        "name": "get_tracked_applications",
        "description": "Mengambil daftar seluruh lamaran yang sedang dipantau di Kanban Tracker (status: saved, preparing, applied, interviewing, offered, rejected).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "description": "Filter status aplikasi tertentu (opsional: 'saved', 'applied', 'interviewing', dll)"
                }
            }
        }
    },
    {
        "name": "update_application_status",
        "description": "Memperbarui status lamaran di Kanban Board (contoh: menandai sudah dilamar, mencatat tanggal wawancara, dsb).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "job_id": {
                    "type": "string",
                    "description": "ID unik lowongan"
                },
                "status": {
                    "type": "string",
                    "enum": ["saved", "preparing", "applied", "interviewing", "offered", "rejected", "archived"],
                    "description": "Status lamaran baru"
                },
                "applied_date": {
                    "type": "string",
                    "description": "Tanggal melamar format YYYY-MM-DD (opsional)"
                },
                "notes": {
                    "type": "string",
                    "description": "Catatan pribadi terkait progres lamaran"
                },
                "follow_up_date": {
                    "type": "string",
                    "description": "Tanggal follow-up berikutnya (opsional)"
                }
            },
            "required": ["job_id", "status"]
        }
    }
]


def handle_get_verified_remote_jobs(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    limit = args.get("limit", 10)
    only_small = args.get("only_small_companies", True)
    jobs = get_all_jobs(status="verified_eligible", freshness_days=14, only_small_companies=only_small)
    return [
        {
            "id": j["id"],
            "title": j["title"],
            "company_name": j["company_name"],
            "match_score": j.get("match_score"),
            "company_size": j.get("company_size_category"),
            "application_url": j.get("application_url"),
            "published_at": j.get("published_at"),
        }
        for j in jobs[:limit]
    ]


def handle_search_remote_jobs(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    query = args["query"].strip()
    min_fit = args.get("min_fit_score", 0)
    limit = args.get("limit", 10)
    freshness = args.get("freshness_days", 30)

    all_jobs = get_all_jobs(status=None, freshness_days=freshness, only_small_companies=False, search=query)
    matched = []
    for j in all_jobs:
        score = j.get("match_score") or 0
        if score < min_fit:
            continue
        matched.append({
            "id": j["id"],
            "title": j["title"],
            "company_name": j["company_name"],
            "eligibility_status": j.get("eligibility_status", "unknown"),
            "match_score": score,
            "application_url": j.get("application_url"),
        })
        if len(matched) >= limit:
            break
    return matched


def handle_get_job_details(args: Dict[str, Any]) -> Dict[str, Any]:
    job_id = args["job_id"]
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT j.*, 
               a.status as application_status, a.applied_date, a.notes as application_notes
        FROM jobs j
        LEFT JOIN job_applications a ON j.id = a.job_id
        WHERE j.id = ?
    """, (job_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return {"error": f"Lowongan dengan ID '{job_id}' tidak ditemukan."}

    return {
        "id": row["id"],
        "source": row["source"],
        "title": row["title"],
        "company_name": row["company_name"],
        "location": row["location"],
        "eligibility_status": row["eligibility_status"],
        "match_score": row["match_score"],
        "match_reasons": json.loads(row["match_reasons"]) if row["match_reasons"] else [],
        "company_size_category": row["company_size_category"],
        "application_url": row["application_url"],
        "application_status": row["application_status"],
        "application_notes": row["application_notes"],
        "description_snippet": (row["description"] or "")[:500] + "..."
    }


def handle_get_tracked_applications(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    status_filter = args.get("status")
    apps = get_all_tracked_applications()
    if status_filter:
        apps = [a for a in apps if a.get("status") == status_filter]
    return apps


def handle_update_application_status(args: Dict[str, Any]) -> Dict[str, Any]:
    job_id = args["job_id"]
    status = args["status"]
    applied_date = args.get("applied_date")
    notes = args.get("notes")
    follow_up_date = args.get("follow_up_date")

    updated = upsert_application(
        job_id=job_id,
        status=status,
        applied_date=applied_date,
        notes=notes,
        follow_up_date=follow_up_date
    )
    if updated:
        return {"success": True, "message": f"Status lowongan {job_id} berhasil diupdate ke '{status}'."}
    return {"success": False, "error": "Gagal menyimpan update aplikasi."}


def process_request(request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Memproses request JSON-RPC 2.0."""
    req_id = request.get("id")
    method = request.get("method")
    params = request.get("params", {})

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "serverInfo": {
                    "name": "remote-job-radar-mcp",
                    "version": "1.0.0"
                }
            }
        }

    elif method == "notifications/initialized":
        return None

    elif method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "tools": TOOLS
            }
        }

    elif method == "tools/call":
        tool_name = params.get("name")
        tool_args = params.get("arguments", {})

        try:
            if tool_name == "get_verified_remote_jobs":
                res = handle_get_verified_remote_jobs(tool_args)
            elif tool_name == "search_remote_jobs":
                res = handle_search_remote_jobs(tool_args)
            elif tool_name == "get_job_details":
                res = handle_get_job_details(tool_args)
            elif tool_name == "get_tracked_applications":
                res = handle_get_tracked_applications(tool_args)
            elif tool_name == "update_application_status":
                res = handle_update_application_status(tool_args)
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32601, "message": f"Tool '{tool_name}' tidak ditemukan"}
                }

            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(res, indent=2, ensure_ascii=False)
                        }
                    ]
                }
            }
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32000, "message": str(e)}
            }

    elif method == "ping":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {}
        }

    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "error": {"code": -32601, "message": f"Method '{method}' tidak dikenali"}
    }


def main():
    """Main loop membaca stdio line by line JSON-RPC."""
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
            resp = process_request(req)
            if resp is not None:
                sys.stdout.write(json.dumps(resp) + "\n")
                sys.stdout.flush()
        except json.JSONDecodeError:
            continue
        except Exception as e:
            logging.error(f"Error handling MCP line: {e}")


if __name__ == "__main__":
    main()
