{ pkgs, ... }:

{
  packages = with pkgs; [ prek ];

  languages.python = {
    enable = true;
    package = pkgs.python312;
    uv.enable = true;
  };

  languages.javascript = {
    enable = true;
    pnpm.enable = true;
  };

  scripts.build-frontend.exec = ''
    cd frontend && pnpm build && cp -r dist/* ../src/qibocal_report/static/ && cp -r ../docs/* ../src/qibocal_report/static/docs/
  '';

  scripts.build-wheel.exec = ''
    uv build
  '';

  scripts.serve.exec = ''
    qibocal report serve sample_data
  '';

  scripts.dashboard.exec = ''
    qibocal report dashboard
  '';

  scripts.test-backend.exec = ''
    pytest tests/
  '';

  enterShell = ''
    if [ -d .venv ]; then
      export PATH="$PWD/.venv/bin:$PATH"
    fi
  '';

  enterTest = ''
    pytest tests/
  '';
}
