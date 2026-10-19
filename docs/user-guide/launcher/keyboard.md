# Desktop Launcher: Keyboard Shortcuts

The keys follow GitHub's: a letter after `g` goes somewhere, and `?` shows the list over any page — the launcher's and the dashboard's alike. Letters work anywhere but in a text field; the menu shortcuts, with their modifier, work everywhere.

| Keys | What |
| --- | --- |
| `g h` | Home |
| `g s` | Servers |
| `g r` | Running |
| `g b` | Notebooks |
| `g c` | Configuration |
| `g n` | Notifications |
| `g q` | Queues |
| `g d` | Dashboard |
| `n` | New server: Servers, with the form open |
| `?` | Show the keyboard shortcuts; `Esc` puts them away |
| `Cmd/Ctrl+Shift+H` | Home, from the Go menu |
| `Cmd/Ctrl+Shift+S`, `+R`, `+B` | Servers, Running, Notebooks, from the Go menu |
| `Cmd/Ctrl+,` | Configuration, from the Go menu — where every application keeps its preferences |
| `Cmd/Ctrl+D` | Dashboard, from the Go menu |
| `Cmd/Ctrl+Shift+N` | Register a server, from the Servers menu |
| `Cmd/Ctrl+/` | Help |
| `Cmd/Ctrl+N` | This page again, in a new window |
| `Cmd/Ctrl++`, `Cmd/Ctrl+-`, `Cmd/Ctrl+0` | Zoom in, zoom out, actual size; the wheel with the key held zooms too |
| `Shift+Enter` | What is under the cursor, in a new window, where `Enter` opens it |

On each page, `j` and `k` walk its list — `h` and `l` too, where there is a side to move to — the entry under the cursor wears an outline, `Enter` does what a click does, and a letter acts on that entry; `Esc` clears the cursor. No key does anything that cannot be undone: a server is started, never forgotten, from the keyboard. The cheatsheet on `?` lists the keys of the page it is opened on, first.

| Page | Keys |
| --- | --- |
| Home | `h`/`j`/`k`/`l` move over the cards as the grid they are, and below the last row over the lines of what runs; `Enter` opens the card, or the card in Running of what runs; `o` opens where what runs is used |
| Servers | `Enter` or `s` opens the server in the dashboard while it runs, starts it otherwise; `e` edits it; `i` invites an administrator; `u` updates its `qibocal-report` and starts it again |
| Running | `j`/`k` move the selection itself; `Enter` or `o` opens it — the dashboard for a server, the browser for a notebook; `x` stops it; `s` starts it again; `r` registers a server started for a look; `l` unfolds its latest run, `h` folds it; `q` opens the SLURM queue of a dispatched session |
| Notebooks | `j`/`k` walk the registered sessions; `Enter` or `s` opens a running one in the browser, or starts it; `e` edits it, `d` duplicates it |
| Configuration | `j`/`k` walk the files; `Enter` opens one, or closes it |
| Notifications | `Enter` goes where it points; `e` marks it done, or brings it back; `x` deletes it |
| Dashboard, everywhere | `g s` the report servers; `g l` the report list of the active server |
| Dashboard, the report list | `/` to the search; `Enter` opens the report; `Esc` leaves the search, or the list |
| Dashboard, a report | `b` back to the search; `v` slideshow or continuous; `j`/`l` and `k`/`h` next and previous protocol; `↑`/`↓` the overview and the last protocol in a slideshow; `d` its documentation; `x` its data; `c` its comments, or the session's; `n`/`o` the new and old platform pages; `w` the live mode |

The header carries no navigation of its own: the logo in the top-left corner returns to the home page, and everything else — the dashboard included — is in the **Go** menu, which works from the dashboard too. Whatever the launcher has to say — a server starting, a link copied, something that failed — is said in the status bar along the bottom edge, which blends into the page: the latest message appears in the bottom-right corner and fades by itself, and the counter next to it opens the list of everything said; an entry about a section is itself the way there, a click anywhere on its text, and the cross archives it; while an error sits in the list, the counter is red. The bubble shows the five most recent of the last day, with their time; its title, and the *more…* row when there are more, open the **Notifications** page, where everything is kept — grouped by the section it is about, as GitHub groups its notifications by repository, each entry dated by its distance from now — and where every entry, or a whole group, can be marked done — put away without being lost — brought back, or deleted. A click anywhere else closes the bubble. Nothing pops up over the page. The bottom-left corner names the `qibocal-report` the launcher drives, with its version and, for its own installation, the commit or release it holds, behind a dot that is green when the command line is there, amber while it is being installed, red while it is missing; it leads to **Configuration**. The **Servers** system menu lists the registered instances: picking one starts it again with the options it was last started with.
