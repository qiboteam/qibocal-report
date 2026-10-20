/**
 * The documentation's table of contents, as the dashboard shows it when the
 * server does not send its own — and the launcher's Help, which shows the
 * Desktop Launcher section of it. No Vue here: the launcher imports it on a
 * page where the dashboard's store does not run.
 */
export const DEFAULT_DOCS_NAV = [
  {
    section: 'Overview',
    path: 'index',
    items: [
      {
        id: 'index',
        path: 'index',
        title: 'Overview & Ecosystem',
        description: 'Introduction to Qibo ecosystem, projects, and qibocal-report architecture'
      }
    ]
  },
  {
    section: 'User Guide',
    path: 'user-guide',
    items: [
      {
        id: 'user-guide/quickstart',
        path: 'user-guide/quickstart',
        title: 'Getting Started & Quickstart',
        description: 'Installation, CLI commands, and report directory structure'
      },
      {
        id: 'user-guide/dashboard',
        path: 'user-guide/dashboard',
        title: 'Dashboard & Server Management',
        description: 'Managing servers, search, smart facets, dual views, and bulk actions'
      },
      {
        id: 'user-guide/reports',
        path: 'user-guide/reports',
        title: 'Reports, Protocols & Exports',
        description: 'Interactive charts, protocol timings, downloads, and PDF printing'
      }
    ]
  },
  {
    section: 'Desktop Launcher',
    path: 'user-guide/launcher',
    items: [
      {
        id: 'user-guide/launcher/installation',
        path: 'user-guide/launcher/installation',
        title: 'Installation',
        description: 'Installers for each platform, opening an unsigned build, and the qibocal-report the launcher drives'
      },
      {
        id: 'user-guide/launcher/sections',
        path: 'user-guide/launcher/sections',
        title: 'Sections & Windows',
        description: 'The sections, several windows, running in the background, and zoom'
      },
      {
        id: 'user-guide/launcher/keyboard',
        path: 'user-guide/launcher/keyboard',
        title: 'Keyboard Shortcuts',
        description: 'GitHub-style keys, the menu shortcuts, and the keys of each page'
      },
      {
        id: 'user-guide/launcher/qibocal-report',
        path: 'user-guide/launcher/qibocal-report',
        title: 'Installing qibocal-report',
        description: "The launcher's own environment, its version, and other environments"
      },
      {
        id: 'user-guide/launcher/servers',
        path: 'user-guide/launcher/servers',
        title: 'Report Servers',
        description: 'Starting and registering servers, here or over SSH, and handling them while they run'
      },
      {
        id: 'user-guide/launcher/notebooks',
        path: 'user-guide/launcher/notebooks',
        title: 'Notebooks & Queues',
        description: 'JupyterLab and Marimo sessions, locally, over SSH or through SLURM, and the queues'
      },
      {
        id: 'user-guide/launcher/remote',
        path: 'user-guide/launcher/remote',
        title: 'Remote Execution',
        description: "Connections for qibocal-widgets' remote executor, and their reports"
      },
      {
        id: 'user-guide/launcher/configuration',
        path: 'user-guide/launcher/configuration',
        title: 'Configuration',
        description: 'The files shared with the command line, their formats, and the web client'
      }
    ]
  },
  {
    section: 'Developer & Architecture',
    path: 'developer',
    items: [
      {
        id: 'developer/architecture',
        path: 'developer/architecture',
        title: 'System Architecture',
        description: 'FastAPI backend, Vue 3 SPA frontend, and execution modes'
      },
      {
        id: 'developer/workflow',
        path: 'developer/workflow',
        title: 'Development Workflow',
        description: 'devenv environment, live Vite HMR, testing, and packaging'
      },
      {
        id: 'developer/design-system',
        path: 'developer/design-system',
        title: 'Design System & Aesthetics',
        description: 'BackMarket design palette, typography, and print media CSS'
      }
    ]
  },
  {
    section: 'Reference',
    path: 'reference',
    items: [
      {
        id: 'reference/cli',
        path: 'reference/cli',
        title: 'CLI Reference',
        description: 'Complete command line options and environment variables'
      },
      {
        id: 'reference/api',
        path: 'reference/api',
        title: 'REST API & WebSockets',
        description: 'REST endpoints specification, schemas, and WebSocket events'
      }
    ]
  }
]

/** The section a page belongs to, by its path; null for none. */
export function docsSection(path, nav = DEFAULT_DOCS_NAV) {
  return nav.find(section => section.path === path || section.items.some(item => item.path === path)) || null
}
