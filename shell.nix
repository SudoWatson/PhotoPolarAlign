let
  pkgs = import <nixpkgs> {};
in pkgs.mkShell {
  packages = [
    (pkgs.python3.withPackages (pyPkgs: [
        pyPkgs.numpy
        pyPkgs.scipy
        pyPkgs.pillow
        pyPkgs.configparser
        pyPkgs.astropy
        pyPkgs.tkinter
    ]))
  ];
}
