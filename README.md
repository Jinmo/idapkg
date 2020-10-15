# Package manager for IDA Pro

> WARNING: This project is still between alpha and beta state. Feel free to report bugs if this is not working!

## How to install

Execute the script below in IDAPython console (minified [`installer.py`](https://github.com/Jinmo/idapkg/raw/master/installer.py).)

```
import zipfile,tempfile,sys,os,threading,shutil,importlib
def install():P=os.path;tag='v0.1.4';n=tempfile.NamedTemporaryFile(delete=False,suffix='.zip');n.close();print('Started downloading idapkg...');importlib.import_module('urllib.request' if sys.version_info.major==3 else 'urllib').urlretrieve('https://github.com/Jinmo/idapkg/archive/%s.zip'%tag,n.name);f=open(n.name,'rb+');f.seek(0,os.SEEK_END);f.truncate(f.tell()-0x28);f.close();z=zipfile.ZipFile(n.name);base=z.namelist()[0];sys.path.append(P.join(n.name,base));from pkg.config import g;import pkg.main as main;packages_path=g['path']['packages'];z.extractall(packages_path);z.close();dest=P.join(packages_path,'idapkg');P.isdir(dest)and shutil.rmtree(dest);os.rename(P.join(packages_path,base),dest);main.update_pythonrc();main.init_environment(False);print('Installation success! Please restart IDA to use idapkg.');os.unlink(n.name)
threading.Thread(target=install).start()
```

Then you can access related actions via command palette (Ctrl+Shift+P on windows/mac/linux, or Command+Shift+P on mac) after restarting IDA Pro.

### Testing latest changes

To test the master branch, you can replace `tag='v...'` into `tag='master'`.

## What file is created

`~(Your home directory)/idapkg`, and some lines in idapythonrc.py will be created.

```
idapkg/
  packages/
  python/
  config.json
```

### packages/

When a package is installed, `packages/<name>` is created and further added to `IDAUSR` variable. This enables following folders to be loaded by IDA Pro.

```
<name>
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
        "https://api.idapkg.com",
        "github:Jinmo/idapkg-repo/master"
    ]
}
```

And you can use your private repo for fetching packages. The api server will be uploaded soon!

## Writing a package

See [Writing a package (link)](https://idapkg.com/getting-started).

## TODO

Currently finding way to reliably and generally [update `IDAUSR` variable on all platforms](https://github.com/Jinmo/idapkg/blob/master/pkg/internal_api/win.py). Currently only supporting Windows and Mac OS X.