import {
  NavigationMenu,
  NavigationMenuItem,
  NavigationMenuLink,
  NavigationMenuList,
  navigationMenuTriggerStyle,
} from "@/components/ui/navigation-menu"
import { ExternalLink } from "lucide-react"
import Link from "next/link"

export function Navbar() {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
  const githubUrl = process.env.NEXT_PUBLIC_GITHUB_URL

  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-14 items-center px-4">
        <div className="mr-4 flex">
          <Link href="/" className="mr-6 flex items-center space-x-2">
            <span className="font-bold text-blue-600 sm:inline-block">
              TennisH2H
            </span>
          </Link>
        </div>
        <NavigationMenu className="md:flex">
          <NavigationMenuList>
            <NavigationMenuItem>
              <NavigationMenuLink asChild className={navigationMenuTriggerStyle()}>
                <Link href="/players">Players</Link>
              </NavigationMenuLink>
            </NavigationMenuItem>
            <NavigationMenuItem>
              <NavigationMenuLink asChild className={navigationMenuTriggerStyle()}>
                <Link href="/matchups">Head to Head</Link>
              </NavigationMenuLink>
            </NavigationMenuItem>
            <NavigationMenuItem>
              <NavigationMenuLink asChild className={navigationMenuTriggerStyle()}>
                <Link href="/rankings">Rankings</Link>
              </NavigationMenuLink>
            </NavigationMenuItem>
          </NavigationMenuList>
        </NavigationMenu>
        <div className="ml-auto flex items-center space-x-4">
          <a
            href={`${apiUrl}/docs`}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1 text-sm font-medium text-muted-foreground hover:text-foreground transition-colors"
          >
            API <ExternalLink className="h-3 w-3" />
          </a>
          {githubUrl && (
            <a
              href={githubUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1 text-sm font-medium text-muted-foreground hover:text-foreground transition-colors"
            >
              GitHub <ExternalLink className="h-3 w-3" />
            </a>
          )}
        </div>
      </div>
    </header>
  )
}

