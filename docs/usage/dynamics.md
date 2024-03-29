# Dynamics

:::{warning}

The {doc}`PWA Expert System <index>` has been split up into
{doc}`QRules <qrules:index>` and {doc}`AmpForm <ampform:index>`. Please use
these packages instead!

:::

By default, the dynamic terms in an amplitude model are set to $1$ by the
{class}`.HelicityAmplitudeBuilder`. The method {meth}`.set_dynamics` can then
be used to set dynamics lineshapes for specific resonances.

In the following pages, we show how to insert custom dynamics and illustrate
some of the lineshapes provided by the {mod}`expertsystem`.

```{toctree}
dynamics/custom
dynamics/lineshapes
```
