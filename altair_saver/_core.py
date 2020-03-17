from collections import OrderedDict
from typing import Any, Dict, IO, Iterable, Optional, Type, Union

import altair as alt

from altair_saver.savers import (
    Saver,
    BasicSaver,
    HTMLSaver,
    NodeSaver,
    SeleniumSaver,
)
from altair_saver._utils import (
    extract_format,
    infer_mode_from_spec,
    JSONDict,
    Mimebundle,
)

_SAVER_METHODS: Dict[str, Type[Saver]] = OrderedDict(
    [
        ("basic", BasicSaver),
        ("html", HTMLSaver),
        ("selenium", SeleniumSaver),
        ("node", NodeSaver),
    ]
)


def _select_saver(
    method: Optional[Union[str, Type[Saver]]],
    mode: str,
    fmt: Optional[str] = None,
    fp: Optional[Union[IO, str]] = None,
) -> Type[Saver]:
    """Get an enabled Saver class that supports the specified format."""
    if isinstance(method, type) and issubclass(method, Saver):
        return method
    elif isinstance(method, str):
        if method in _SAVER_METHODS:
            return _SAVER_METHODS[method]
        else:
            raise ValueError(f"Unrecognized method: {method!r}")
    elif method is None:
        if fmt is None:
            if fp is None:
                raise ValueError("Either fmt or fp must be specified")
            fmt = extract_format(fp)
        for s in _SAVER_METHODS.values():
            if s.enabled() and fmt in s.valid_formats[mode]:
                return s
        raise ValueError(f"No enabled saver found that supports format={fmt!r}")
    else:
        raise ValueError(f"Unrecognized method: {method}")


def save(
    chart: Union[alt.TopLevelMixin, JSONDict],
    fp: Union[IO, str],
    fmt: Optional[str] = None,
    mode: Optional[str] = None,
    embed_options: Optional[JSONDict] = None,
    method: Optional[Union[str, type]] = None,
    **kwargs: Any,
) -> None:
    """Save an Altair, Vega, or Vega-Lite chart

    Parameters
    ----------
    chart : alt.Chart or dict
        The chart or Vega/Vega-Lite chart specification to be saved
    fp : file or filename
        location to save the result.
    fmt : string (optinoal)
        The format in which to save the chart. If not specified and fp is a string,
        fmt will be determined from the file extension. Options are
        ["html", "pdf", "png", "svg", "vega", "vega-lite"].
    mode : string (optional)
        The mode of the input spec. Either "vega-lite" or "vega". If not specified,
        it will be inferred from the spec.
    embed_options : dict (optional)
        A dictionary of options to pass to vega-embed. If not specified, the default
        will be drawn from alt.renderers.options.
    method : string or type
        The save method to use: one of {"node", "selenium", "html", "basic"},
        or a subclass of Saver.

    Additional Parameters
    ---------------------
    vega_version : string (optional)
        For method in {"selenium", "html"}, the version of the vega javascript
        package to use. Default is alt.VEGA_VERSION.
    vegalite_version : string (optional)
        For method in {"selenium", "html"}, the version of the vega-lite javascript
        package to use. Default is alt.VEGALITE_VERSION.
    vegaembed_version : string (optional)
        For method in {"selenium", "html"}, the version of the vega-embed javascript
        package to use. Default is alt.VEGAEMBED_VERSION.
    inline : boolean (optional)
        For method="html", specify whether javascript sources should be included
        inline rather than loaded from an external CDN. Default: False.
    standalone : boolean (optional)
        For method="html", specify whether to create a standalone HTML file.
        Default is True for save().
    webdriver : string or Object (optional)
        For method="selenium", the type of webdriver to use: one of "chrome", "firefox",
        or a selenium.WebDriver object. Defaults to what is available on your system.
    offline : bool (optional)
        For method="selenium", whether to save charts in offline mode (default=True). If
        false, saving charts will require a web connection to load Javascript from CDN.
    **kwargs :
        Additional keyword arguments are passed to Saver initialization.
    """
    spec: JSONDict = {}
    if isinstance(chart, dict):
        spec = chart
    else:
        spec = chart.to_dict()

    if mode is None:
        mode = infer_mode_from_spec(spec)

    if embed_options is None:
        embed_options = alt.renderers.options.get("embed_options", None)

    Saver = _select_saver(method, mode=mode, fmt=fmt, fp=fp)
    saver = Saver(spec, mode=mode, embed_options=embed_options, **kwargs)

    saver.save(fp=fp, fmt=fmt)


def render(
    chart: Union[alt.TopLevelMixin, JSONDict],
    fmts: Union[str, Iterable[str]],
    mode: Optional[str] = None,
    embed_options: Optional[JSONDict] = None,
    method: Optional[Union[str, type]] = None,
    **kwargs: Any,
) -> Mimebundle:
    """Render a chart, returning a mimebundle.

    Parameters
    ----------
    chart : alt.Chart or dict
        The chart or Vega/Vega-Lite chart specification
    fmts : string or list of strings
        The format(s) to include in the mimebundle. Options are
        ["html", "pdf", "png", "svg", "vega", "vega-lite"].
    mode : string (optional)
        The mode of the input spec. Either "vega-lite" or "vega". If not specified,
        it will be inferred from the spec.
    embed_options : dict (optional)
        A dictionary of options to pass to vega-embed. If not specified, the default
        will be drawn from alt.renderers.options.
    method : string or type
        The save method to use: one of {"node", "selenium", "html", "basic"},
        or a subclass of Saver.

    Additional Parameters
    ---------------------
    vega_version : string (optional)
        For method in {"selenium", "html"}, the version of the vega javascript
        package to use. Default is alt.VEGA_VERSION.
    vegalite_version : string (optional)
        For method in {"selenium", "html"}, the version of the vega-lite javascript
        package to use. Default is alt.VEGALITE_VERSION.
    vegaembed_version : string (optional)
        For method in {"selenium", "html"}, the version of the vega-embed javascript
        package to use. Default is alt.VEGAEMBED_VERSION.
    inline : boolean (optional)
        For method="html", specify whether javascript sources should be included
        inline rather than loaded from an external CDN. Default: False.
    standalone : boolean (optional)
        For method="html", specify whether to create a standalone HTML file.
        Default is False for render().
    webdriver : string or Object (optional)
        For method="selenium", the type of webdriver to use: one of "chrome", "firefox",
        or a selenium.WebDriver object. Defaults to what is available on your system.
    offline : bool (optional)
        For method="selenium", whether to save charts in offline mode (default=True). If
        false, saving charts will require a web connection to load Javascript from CDN.
    **kwargs :
        Additional keyword arguments are passed to Saver initialization.
    """
    if isinstance(fmts, str):
        fmts = [fmts]
    mimebundle: Mimebundle = {}

    spec: JSONDict = {}
    if isinstance(chart, dict):
        spec = chart
    else:
        spec = chart.to_dict()

    if mode is None:
        mode = infer_mode_from_spec(spec)

    if embed_options is None:
        embed_options = alt.renderers.options.get("embed_options", None)

    for fmt in fmts:
        Saver = _select_saver(method, mode=mode, fmt=fmt)
        saver = Saver(spec, mode=mode, embed_options=embed_options, **kwargs)
        mimebundle.update(saver.mimebundle(fmt))

    return mimebundle
