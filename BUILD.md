# Build steps

1. Install old version of setuptools and twine

```bash
pip install setuptools==54.2.0 --force-reinstall --no-cache-dir
pip install twine==3.4.0
```

2. Build:

> [!NOTE]
> Make sure to update the version number before you build

```bash
python setup.py sdist bdist_wheel
```

3. Publish

```bash
python -m twine upload dist/*
```
