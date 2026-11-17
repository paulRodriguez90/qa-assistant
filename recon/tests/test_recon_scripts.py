"""Tests de los scripts de reconocimiento. No necesitan red, MobSF ni dispositivo."""
import json
from pathlib import Path

import pytest

from recon.findings import Finding, write_findings
from recon.mobile import layouts, logcat_summary, manifest, mobsf_scan
from recon.web import har_summary

FIXTURES = Path(__file__).parent / "fixtures"


def _ids(findings):
    return {f.id for f in findings}


@pytest.mark.smoke
def test_write_findings_marca_solo_los_nuevos(tmp_path):
    """Una segunda corrida marca como nuevos solo los hallazgos que no estaban."""
    destino = tmp_path / "f.json"
    base = Finding(id="a", titulo="A", categoria="x", severidad="baja", evidencia="visto", fuente="t")
    write_findings(destino, "demo", "t", [base])
    nuevo = Finding(id="b", titulo="B", categoria="x", severidad="alta", evidencia="visto", fuente="t")
    data = write_findings(destino, "demo", "t", [base, nuevo])
    assert data["nuevos"] == 1
    assert [h["id"] for h in data["hallazgos"]] == ["b", "a"]  # ordenado por severidad
    assert {h["id"]: h["nuevo"] for h in data["hallazgos"]} == {"a": False, "b": True}


@pytest.mark.regression
def test_finding_con_evidencia_invalida_falla():
    """La evidencia solo puede ser visto, inferido o desconocido."""
    with pytest.raises(ValueError):
        Finding(id="a", titulo="A", categoria="x", severidad="baja", evidencia="seguro", fuente="t")


@pytest.mark.smoke
def test_har_summary_detecta_errores_y_lentitud():
    """El HAR de ejemplo produce un 5xx, un 4xx, un endpoint lento y datos sensibles en la URL."""
    har = json.loads((FIXTURES / "sample.har").read_text(encoding="utf-8"))
    findings, resumen = har_summary.summarize(har)
    ids = _ids(findings)
    assert "http-5xx:POST shop.example.test/api/cart" in ids
    assert "http-4xx:GET shop.example.test/api/items:422" in ids
    assert "lento:GET shop.example.test/api/items" in ids
    assert "dato-sensible-url:POST shop.example.test/api/cart" in ids
    assert "http-plano:cdn.example.test" in ids
    assert "headers-seguridad:shop.example.test" in ids
    assert not any("api/me" in i for i in ids)  # 401 es esperado sin sesión
    assert resumen["endpoints"]["POST shop.example.test/api/cart"]["llamadas"] == 2


@pytest.mark.regression
def test_har_summary_no_copia_valores_sensibles():
    """El resumen nombra el parámetro sensible pero nunca su valor."""
    har = json.loads((FIXTURES / "sample.har").read_text(encoding="utf-8"))
    findings, resumen = har_summary.summarize(har)
    texto = json.dumps([f.__dict__ for f in findings]) + json.dumps(resumen)
    assert "token" in texto
    assert "abc" not in texto


@pytest.mark.smoke
def test_mobsf_summary_filtra_info_y_no_copia_secretos():
    """Del reporte de MobSF quedan solo hallazgos media/alta, y los secretos solo se cuentan."""
    report = json.loads((FIXTURES / "mobsf_report.json").read_text(encoding="utf-8"))
    findings, resumen = mobsf_scan.summarize(report)
    ids = _ids(findings)
    assert "manifest:exported_activity:com.ejemplo.app.DeepLinkActivity" in ids
    assert "manifest:app_allowbackup:" in ids
    assert "codigo:android_insecure_random" in ids
    assert "codigo:android_logging" not in ids
    assert not any(i.startswith("manifest:info_rule") for i in ids)
    assert "secretos" in ids
    assert "no-es-real-123" not in json.dumps([f.__dict__ for f in findings])
    permisos = next(f for f in findings if f.id == "permisos-peligrosos")
    assert permisos.extra["permisos"] == ["android.permission.CAMERA"]
    assert resumen["paquete"] == "com.ejemplo.app"
    assert all(f.evidencia == "inferido" for f in findings)


@pytest.mark.smoke
def test_layouts_detecta_botones_sin_descripcion():
    """Un ImageButton sin contentDescription es un hallazgo; uno con descripción o decorativo no."""
    findings, resumen = layouts.analyze(FIXTURES / "apktool")
    assert _ids(findings) == {"a11y:activity_cart:btn_delete", "a11y:item_rating:ImageView#1",
                              "a11y:item_rating:ImageView#2"}
    pantalla = resumen["pantallas"]["activity_cart"]
    assert "btn_checkout" in pantalla["ids"]
    assert pantalla["content_desc"] == ["Volver"]


@pytest.mark.regression
def test_layouts_junta_variantes_del_mismo_layout():
    """layout/ y layout-v22/ del mismo archivo dan un solo hallazgo con las dos variantes."""
    findings, _ = layouts.analyze(FIXTURES / "apktool")
    borrar = next(f for f in findings if f.id == "a11y:activity_cart:btn_delete")
    assert borrar.extra["variantes"] == ["layout", "layout-v22"]


@pytest.mark.regression
def test_layouts_omite_layouts_de_librerias():
    """Los layouts de AndroidX/Material (abc_, mtrl_...) se omiten salvo que se pidan."""
    findings, resumen = layouts.analyze(FIXTURES / "apktool")
    assert "abc_action_bar" not in resumen["pantallas"]
    assert resumen["omitidos_de_librerias"] == 1
    con_librerias, _ = layouts.analyze(FIXTURES / "apktool", incluir_librerias=True)
    assert "a11y:abc_action_bar:abc_home" in _ids(con_librerias)


@pytest.mark.smoke
def test_manifest_detecta_debuggable_backup_y_exportados():
    """Sin MobSF, el manifiesto de apktool alcanza para ver debuggable, backup y exportados sin permiso."""
    findings, resumen = manifest.analyze(FIXTURES / "apktool")
    ids = _ids(findings)
    assert {"manifest:debuggable", "manifest:allowBackup", "manifest:cleartext"} <= ids
    assert "exportado:com.ejemplo.app.DeepLinkActivity" in ids
    assert "exportado:com.ejemplo.app.PushReceiver" in ids  # intent-filter sin exported explícito
    assert "exportado:com.ejemplo.app.DataProvider" in ids
    assert "exportado:com.ejemplo.app.MainActivity" not in ids  # launcher
    assert "exportado:com.ejemplo.app.SyncService" not in ids  # protegido con permiso
    debug = next(f for f in findings if f.id == "manifest:componentes-debug")
    assert debug.extra["componentes"] == ["com.ejemplo.app.debug.DebugCrashActivity"]
    assert resumen["permisos"] == ["android.permission.CAMERA"]


@pytest.mark.smoke
def test_logcat_detecta_crash_y_anr_de_la_app():
    """Se reportan el crash y el ANR del paquete indicado, no los de otras apps."""
    texto = (FIXTURES / "logcat.txt").read_text(encoding="utf-8")
    findings, conteo = logcat_summary.analyze(texto, "com.ejemplo.app")
    assert conteo == {"crashes": 1, "anr": 1}
    crash = next(f for f in findings if f.categoria == "crash")
    assert crash.extra["excepcion"] == "java.lang.NullPointerException"
    assert crash.ubicacion == "com.ejemplo.app.cart.CartActivity.onCheckout(CartActivity.java:88)"
    assert all(f.evidencia == "visto" for f in findings)


@pytest.mark.smoke
def test_har_summary_reporta_errores_de_consola():
    """Una excepción JS capturada durante los tests se reporta como hallazgo visto."""
    har = json.loads((FIXTURES / "sample.har").read_text(encoding="utf-8"))
    findings, _ = har_summary.summarize(har)
    consola = [f for f in findings if f.categoria == "error-consola"]
    assert len(consola) == 1
    assert consola[0].severidad == "alta"
    assert "price" in consola[0].detalle


@pytest.mark.regression
def test_mask_url_oculta_parametros_sensibles():
    """Los valores de token o password en la URL se reemplazan por ***; el resto queda igual."""
    url = har_summary.mask_url("https://x.test/a?token=abc&page=2&Password=p1")
    assert "abc" not in url and "p1" not in url
    assert "page=2" in url and "token=***" in url
