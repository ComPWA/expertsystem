# Installation

:::{warning}

The {doc}`PWA Expert System <index>` has been split up into
{doc}`QRules <qrules:index>` and {doc}`AmpForm <ampform:index>`. Please use
these packages instead!

:::

The fastest way of installing this package is through PyPI:

```shell
python3 -m pip install expertsystem
```

This installs the
[latest, stable release](https://pypi.org/project/expertsystem) that you can
find on the [`stable`](https://github.com/ComPWA/expertsystem/tree/stable)
branch. The latest version on the
[`main`](https://github.com/ComPWA/expertsystem/tree/main) branch can be
installed as follows:

```shell
python3 -m pip install git+https://github.com/ComPWA/expertsystem@main
```

In that case, however, we highly recommend using the more dynamic
{ref}`'editable installation' <pwa:develop:Editable installation>` instead.
This goes as follows:

:::{margin}

```{seealso}

{doc}`pwa:software/git`

```

:::

1. Get the source code:

   ```shell
   git clone https://github.com/ComPWA/expertsystem.git
   cd expertsystem
   ```

2. **[Recommended]** Create a virtual environment (see
   {ref}`here <pwa:develop:Virtual environment>`).

3. Install the project as an
   {ref}`'editable installation' <pwa:develop:Editable installation>` and
   install {ref}`additional packages <pwa:develop:Optional dependencies>` for
   the developer:

   ```shell
   python3 -m pip install -e .[dev]
   ```

   :::{dropdown} Pinning dependency versions

   In order to install the _exact same versions_ of the dependencies with which
   the framework has been tested, use the provided
   [constraints files](https://pip.pypa.io/en/stable/user_guide/#constraints-files)
   for the specific Python version `3.x` you are using:

   ```shell
   python3 -m pip install -c .constraints/py3.x.txt -e .[dev]
   ```

   ```{seealso}

   {ref}`develop:Pinning dependency versions`

   ```

   :::

That's all! Have a look at the {doc}`/usage` page to try out the package. You
can also have a look at the {doc}`pwa:develop` page for tips on how to work
with this 'editable' developer setup!
