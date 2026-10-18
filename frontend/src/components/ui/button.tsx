import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-lg text-xs font-semibold ring-offset-background transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg]:size-4 [&_svg]:shrink-0 cursor-pointer select-none",
  {
    variants: {
      variant: {
        default: "bg-emerald-600 text-white shadow-sm hover:bg-emerald-500 active:scale-[0.98]",
        destructive: "bg-red-600 text-white hover:bg-red-500 shadow-sm",
        outline: "border border-slate-700/80 bg-slate-900/60 hover:bg-slate-800 text-slate-200 hover:text-white shadow-sm",
        secondary: "bg-slate-800 text-slate-200 hover:bg-slate-700/80 hover:text-white border border-slate-700/50",
        ghost: "hover:bg-slate-800/80 text-slate-300 hover:text-white",
        link: "text-emerald-400 underline-offset-4 hover:underline",
        primary: "bg-indigo-600 text-white shadow-sm hover:bg-indigo-500 active:scale-[0.98]",
      },
      size: {
        default: "h-9 px-4 py-2",
        sm: "h-8 rounded-md px-3 text-[11px]",
        lg: "h-10 rounded-lg px-6 text-sm",
        icon: "h-8 w-8 rounded-lg",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button"
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    )
  }
)
Button.displayName = "Button"

export { Button, buttonVariants }
