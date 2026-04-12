import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

const badgeVariants = cva(
  "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
  {
    variants: {
      variant: {
        default: "border-transparent bg-primary text-primary-foreground",
        secondary: "border-transparent bg-secondary text-secondary-foreground",
        destructive: "border-transparent bg-destructive text-destructive-foreground",
        outline: "text-foreground",
        success: "border-transparent bg-grade-a text-primary-foreground",
        warning: "border-transparent bg-grade-c text-primary-foreground",
        danger: "border-transparent bg-grade-d text-primary-foreground",
        info: "border-transparent bg-grade-b text-primary-foreground",
        // Gate layer variants
        redline: "border-transparent bg-gate-redline text-primary-foreground",
        mandatory: "border-transparent bg-gate-mandatory text-primary-foreground",
        suggested: "border-transparent bg-gate-suggested text-primary-foreground",
        gateInfo: "border-transparent bg-gate-info text-primary-foreground",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
)

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return <div className={cn(badgeVariants({ variant }), className)} {...props} />
}

export { Badge, badgeVariants }
