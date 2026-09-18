"""Template globals shared by every render.

`fullname` used to be passed as a keyword argument from four separate routes, and
was `None` for any user row without one — which crashed the nav avatar on
`fullname[:1]`. `asset_v` busts the browser cache for CSS/JS; without a build
step there is nothing else to fingerprint the files with.
"""

import os

from flask import session


def _static_version(static_folder):
    """Newest mtime under static/, as a short string. Falls back to '1'."""
    newest = 0.0
    try:
        for root, _dirs, files in os.walk(static_folder):
            for name in files:
                mtime = os.path.getmtime(os.path.join(root, name))
                if mtime > newest:
                    newest = mtime
    except OSError:
        return "1"
    return str(int(newest)) if newest else "1"


def register_context(app):

    cached = _static_version(app.static_folder)

    @app.context_processor
    def inject_globals():
        # Recompute every request in debug so edits show up without a restart.
        version = _static_version(app.static_folder) if app.debug else cached

        return {
            "fullname": session.get("fullname") or "Pengguna",
            "asset_v": version,
        }
