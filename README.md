# Package manager for IDA Pro

> WARNING: This project is still between alpha and beta state. Feel free to report bugs if this is not working!

## How to install

[Download repo](https://github.com/Jinmo/idapkg/archive/master.zip), and copy `idapkg.py`, `pkg` folder to `<IDA installation dir>/plugins` directory. After restarting IDA, it'll automatically install dependencies and add commands.

Then you can access it via command palette (Ctrl+Shift+P on windows/mac/linux, or Command+Shift+P on mac) after restarting IDA again (due to bug, currently resolving it).

## What file is created

`~(Your home directory)/idapkg` will be created.

```
idapkg/
  packages/
  python/
  config.json
```

### packages/

When a package is installed, `packages/<name>` is created and further added to `IDAUSR` variable. This enables following folders to be loaded by IDA Pro.

```
  plugins/
  procs/
  loaders/
  til/
  sig/
  ids/
```

### python/ - virtualenv

To manage PIP packages easily, this creates a virtualenv and creates `pip`, `easy_install` and other virtalenv-related files and activates the environment.

TL;DR If you run `pip install`, they are installed into `python/lib/*` (`Lib` on windows, all same.)

### config.json

In fact, all paths above are configurable!

```json
{
    "path": {
        "virtualenv": "...\\idapkg\\python", 
        "packages": "...\\idapkg\\packages"
    }, 
    "repos": [
        "https://api.idapkg.com"
    ]
}
```

And you can use your private repo for fetching packages. The api server will be uploaded soon!

## Writing a package

See [Writing a package (link)](https://idapkg.com/getting-started).

## TODO

Currently finding way to reliably and generally [update `IDAUSR` variable on all platforms](https://github.com/Jinmo/idapkg/blob/master/pkg/internal_api/win.py). Currently only supporting Windows.