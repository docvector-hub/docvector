"use client";

export default function LogoOptionsPage() {
  return (
    <div className="min-h-screen p-8" style={{ background: "var(--background)", color: "var(--foreground)" }}>
      <h1 className="text-3xl font-bold mb-8 text-center">DocVector Logo Options</h1>
      <p className="text-center text-gray-500 dark:text-gray-400 mb-12">Click on a logo to see it larger. Pick your favorite!</p>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 max-w-6xl mx-auto">
        {/* Option 1: Document with Search Overlay */}
        <LogoCard title="Option 1: Document Search" description="Document icon with magnifying glass overlay">
          <svg width="80" height="80" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
            <defs>
              <linearGradient id="grad1" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#06b6d4"/>
                <stop offset="100%" stopColor="#8b5cf6"/>
              </linearGradient>
            </defs>
            <rect x="2" y="2" width="44" height="44" rx="10" fill="url(#grad1)"/>
            {/* Document shape */}
            <path d="M14 10h12l8 8v20H14V10z" fill="white"/>
            <path d="M26 10v8h8" fill="none" stroke="white" strokeWidth="2"/>
            {/* Small magnifying glass */}
            <circle cx="32" cy="32" r="6" stroke="white" strokeWidth="2.5" fill="url(#grad1)"/>
            <path d="M36 36L42 42" stroke="white" strokeWidth="2.5" strokeLinecap="round"/>
          </svg>
        </LogoCard>

        {/* Option 2: Abstract D with Vector Arrow */}
        <LogoCard title="Option 2: Vector D" description="Stylized D with directional vector arrow">
          <svg width="80" height="80" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
            <defs>
              <linearGradient id="grad2" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#06b6d4"/>
                <stop offset="100%" stopColor="#8b5cf6"/>
              </linearGradient>
            </defs>
            <rect x="2" y="2" width="44" height="44" rx="10" fill="url(#grad2)"/>
            {/* Bold D shape */}
            <path d="M14 12h8c7.732 0 14 6.268 14 14s-6.268 14-14 14h-8V12z" fill="white"/>
            <path d="M18 16h4c5.523 0 10 4.477 10 10s-4.477 10-10 10h-4V16z" fill="url(#grad2)"/>
            {/* Vector arrow pointing right */}
            <path d="M22 24h10m0 0l-4-4m4 4l-4 4" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        </LogoCard>

        {/* Option 3: Hexagon Tech */}
        <LogoCard title="Option 3: Hexagon" description="Modern hexagonal tech design">
          <svg width="80" height="80" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
            <defs>
              <linearGradient id="grad3" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#06b6d4"/>
                <stop offset="100%" stopColor="#8b5cf6"/>
              </linearGradient>
            </defs>
            <rect x="2" y="2" width="44" height="44" rx="10" fill="url(#grad3)"/>
            {/* Hexagon */}
            <path d="M24 8L38 16v16L24 40L10 32V16L24 8z" fill="white"/>
            <path d="M24 12L34 18v12L24 36L14 30V18L24 12z" fill="url(#grad3)"/>
            {/* D inside */}
            <path d="M18 18h4c3.314 0 6 2.686 6 6s-2.686 6-6 6h-4V18z" fill="white"/>
          </svg>
        </LogoCard>

        {/* Option 4: Layered Documents (Vector Embeddings) */}
        <LogoCard title="Option 4: Vector Layers" description="Stacked layers representing embeddings">
          <svg width="80" height="80" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
            <defs>
              <linearGradient id="grad4" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#06b6d4"/>
                <stop offset="100%" stopColor="#8b5cf6"/>
              </linearGradient>
            </defs>
            <rect x="2" y="2" width="44" height="44" rx="10" fill="url(#grad4)"/>
            {/* Stacked layers */}
            <path d="M24 10L40 18L24 26L8 18L24 10z" fill="white" fillOpacity="0.5"/>
            <path d="M24 18L40 26L24 34L8 26L24 18z" fill="white" fillOpacity="0.75"/>
            <path d="M24 26L40 34L24 42L8 34L24 26z" fill="white"/>
            {/* Center dot */}
            <circle cx="24" cy="34" r="3" fill="url(#grad4)"/>
          </svg>
        </LogoCard>

        {/* Option 5: Neural/Node Network */}
        <LogoCard title="Option 5: Neural Net" description="AI-inspired connected nodes">
          <svg width="80" height="80" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
            <defs>
              <linearGradient id="grad5" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#06b6d4"/>
                <stop offset="100%" stopColor="#8b5cf6"/>
              </linearGradient>
            </defs>
            <rect x="2" y="2" width="44" height="44" rx="10" fill="url(#grad5)"/>
            {/* Connection lines */}
            <path d="M12 16L24 24M12 32L24 24M36 16L24 24M36 32L24 24" stroke="white" strokeWidth="2" strokeOpacity="0.5"/>
            {/* Nodes */}
            <circle cx="12" cy="16" r="4" fill="white"/>
            <circle cx="12" cy="32" r="4" fill="white"/>
            <circle cx="36" cy="16" r="4" fill="white"/>
            <circle cx="36" cy="32" r="4" fill="white"/>
            <circle cx="24" cy="24" r="6" fill="white"/>
            {/* Center D */}
            <text x="24" y="28" fontSize="10" fontWeight="bold" fill="url(#grad5)" textAnchor="middle">D</text>
          </svg>
        </LogoCard>

        {/* Option 6: Book with Lens */}
        <LogoCard title="Option 6: Book Lens" description="Open book with search lens">
          <svg width="80" height="80" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
            <defs>
              <linearGradient id="grad6" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#06b6d4"/>
                <stop offset="100%" stopColor="#8b5cf6"/>
              </linearGradient>
            </defs>
            <rect x="2" y="2" width="44" height="44" rx="10" fill="url(#grad6)"/>
            {/* Open book */}
            <path d="M24 14v24M10 12c4 0 10 2 14 4v24c-4-2-10-4-14-4V12z" fill="white"/>
            <path d="M38 12c-4 0-10 2-14 4v24c4-2 10-4 14-4V12z" fill="white" fillOpacity="0.8"/>
            {/* Small magnifying glass */}
            <circle cx="30" cy="24" r="5" stroke="url(#grad6)" strokeWidth="2" fill="none"/>
            <path d="M34 28L38 32" stroke="url(#grad6)" strokeWidth="2" strokeLinecap="round"/>
          </svg>
        </LogoCard>

        {/* Option 7: Compass/Direction */}
        <LogoCard title="Option 7: Compass" description="Navigation compass for finding docs">
          <svg width="80" height="80" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
            <defs>
              <linearGradient id="grad7" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#06b6d4"/>
                <stop offset="100%" stopColor="#8b5cf6"/>
              </linearGradient>
            </defs>
            <rect x="2" y="2" width="44" height="44" rx="10" fill="url(#grad7)"/>
            {/* Compass circle */}
            <circle cx="24" cy="24" r="14" stroke="white" strokeWidth="3" fill="none"/>
            {/* Compass needle */}
            <path d="M24 10L28 24L24 38L20 24L24 10z" fill="white"/>
            <path d="M24 10L28 24H20L24 10z" fill="white" fillOpacity="0.6"/>
            {/* Center */}
            <circle cx="24" cy="24" r="3" fill="url(#grad7)"/>
          </svg>
        </LogoCard>

        {/* Option 8: Bracket Code Style */}
        <LogoCard title="Option 8: Code Brackets" description="Developer-focused code brackets">
          <svg width="80" height="80" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
            <defs>
              <linearGradient id="grad8" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#06b6d4"/>
                <stop offset="100%" stopColor="#8b5cf6"/>
              </linearGradient>
            </defs>
            <rect x="2" y="2" width="44" height="44" rx="10" fill="url(#grad8)"/>
            {/* Left bracket */}
            <path d="M16 12L10 24L16 36" stroke="white" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" fill="none"/>
            {/* Right bracket */}
            <path d="M32 12L38 24L32 36" stroke="white" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" fill="none"/>
            {/* D in center */}
            <text x="24" y="29" fontSize="14" fontWeight="bold" fill="white" textAnchor="middle">D</text>
          </svg>
        </LogoCard>

        {/* Option 9: Cube/3D */}
        <LogoCard title="Option 9: 3D Cube" description="Dimensional cube representing vector space">
          <svg width="80" height="80" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
            <defs>
              <linearGradient id="grad9" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#06b6d4"/>
                <stop offset="100%" stopColor="#8b5cf6"/>
              </linearGradient>
            </defs>
            <rect x="2" y="2" width="44" height="44" rx="10" fill="url(#grad9)"/>
            {/* 3D cube */}
            <path d="M24 8L38 16L38 32L24 40L10 32L10 16L24 8z" fill="white" fillOpacity="0.3"/>
            <path d="M24 8L38 16L24 24L10 16L24 8z" fill="white"/>
            <path d="M24 24L38 16L38 32L24 40L24 24z" fill="white" fillOpacity="0.7"/>
            <path d="M24 24L10 16L10 32L24 40L24 24z" fill="white" fillOpacity="0.5"/>
          </svg>
        </LogoCard>

        {/* Option 10: Minimal D */}
        <LogoCard title="Option 10: Minimal D" description="Clean, minimal letter D">
          <svg width="80" height="80" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
            <defs>
              <linearGradient id="grad10" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#06b6d4"/>
                <stop offset="100%" stopColor="#8b5cf6"/>
              </linearGradient>
            </defs>
            <rect x="2" y="2" width="44" height="44" rx="10" fill="url(#grad10)"/>
            {/* Bold D */}
            <path d="M14 10h10c8.837 0 16 7.163 16 16s-7.163 16-16 16H14V10z" fill="white"/>
            <path d="M20 16h4c5.523 0 10 4.477 10 10s-4.477 10-10 10h-4V16z" fill="url(#grad10)"/>
          </svg>
        </LogoCard>

        {/* Option 11: Target/Focus */}
        <LogoCard title="Option 11: Target" description="Target/crosshair for precision search">
          <svg width="80" height="80" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
            <defs>
              <linearGradient id="grad11" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#06b6d4"/>
                <stop offset="100%" stopColor="#8b5cf6"/>
              </linearGradient>
            </defs>
            <rect x="2" y="2" width="44" height="44" rx="10" fill="url(#grad11)"/>
            {/* Concentric circles */}
            <circle cx="24" cy="24" r="14" stroke="white" strokeWidth="2" fill="none"/>
            <circle cx="24" cy="24" r="8" stroke="white" strokeWidth="2" fill="none"/>
            <circle cx="24" cy="24" r="3" fill="white"/>
            {/* Crosshair lines */}
            <path d="M24 6v8M24 34v8M6 24h8M34 24h8" stroke="white" strokeWidth="2" strokeLinecap="round"/>
          </svg>
        </LogoCard>

        {/* Option 12: Spark/AI */}
        <LogoCard title="Option 12: AI Spark" description="Spark representing AI intelligence">
          <svg width="80" height="80" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
            <defs>
              <linearGradient id="grad12" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#06b6d4"/>
                <stop offset="100%" stopColor="#8b5cf6"/>
              </linearGradient>
            </defs>
            <rect x="2" y="2" width="44" height="44" rx="10" fill="url(#grad12)"/>
            {/* Four-pointed star/spark */}
            <path d="M24 6L26 20L40 24L26 28L24 42L22 28L8 24L22 20L24 6z" fill="white"/>
            {/* Small accent stars */}
            <circle cx="34" cy="14" r="2" fill="white" fillOpacity="0.6"/>
            <circle cx="14" cy="34" r="1.5" fill="white" fillOpacity="0.4"/>
          </svg>
        </LogoCard>
      </div>

      <div className="mt-16 text-center">
        <p className="text-gray-500 dark:text-gray-400">Tell me which option you prefer, or describe what changes you&apos;d like!</p>
      </div>
    </div>
  );
}

function LogoCard({ title, description, children }: { title: string; description: string; children: React.ReactNode }) {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-lg hover:shadow-xl transition-shadow cursor-pointer border border-gray-200 dark:border-gray-700">
      <div className="flex justify-center mb-4">
        {children}
      </div>
      <h3 className="font-semibold text-lg text-center mb-1">{title}</h3>
      <p className="text-sm text-gray-500 dark:text-gray-400 text-center">{description}</p>
    </div>
  );
}
