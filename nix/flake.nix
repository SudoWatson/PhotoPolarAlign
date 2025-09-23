{
  description = "Development environment for PhotoPolarAlign on Nix";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-25.05";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs { inherit system; };
      in {
        devShells.default = pkgs.mkShell {
          packages = [
            (pkgs.python3.withPackages (pyPkgs: [
              pyPkgs.numpy
              pyPkgs.scipy
              pyPkgs.pillow
              pyPkgs.configparser
              pyPkgs.astropy
              pyPkgs.tkinter
              pyPkgs.platformdirs
              pyPkgs.pyinstaller # For building, not needed for running
            ]))
          ];
        };
      });
}
