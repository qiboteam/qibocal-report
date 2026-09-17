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
    cd frontend && pnpm build && rm -rf ../src/qibocal_report/static/* && cp -r dist/* ../src/qibocal_report/static/
  '';

  scripts.dev.exec = ''
    qibocal report dev sample_data
  '';

  scripts.build-wheel.exec = ''
    uv build
  '';


  scripts.server.exec = ''
    qibocal report server sample_data
  '';

  scripts.client.exec = ''
    qibocal report client
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
