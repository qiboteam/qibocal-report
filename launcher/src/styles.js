/**
 * The stylesheets of both pages.
 *
 * `virtual:uno.css` has to be imported from a single module: with one import
 * per entry point, the global build mode keeps the first occurrence and warns
 * about the others, and the two pages would not be guaranteed the same sheet.
 */
import 'virtual:uno.css'
// The very stylesheet the web frontend uses, so the two halves of the
// application share one look.
import '@dashboard/assets/style.css'
import './assets/launcher.css'
