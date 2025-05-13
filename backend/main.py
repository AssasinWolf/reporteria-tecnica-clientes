
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from utils import cargar_csv
import pandas as pd
import logging
import traceback

app = FastAPI()
logger = logging.getLogger("app")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def normalizar_texto(texto):
    return " ".join(w.capitalize() for w in str(texto).replace("_", " ").replace("-", " ").split())

@app.get("/resumen_tecnicos")
def resumen_tecnicos():
    try:
        df = cargar_csv()
        df["tecnico"] = df["tecnico"].fillna("Sin Técnico").apply(normalizar_texto)
        df["ticket"] = df["ticket"].fillna("SIN_TICKET")
        df["fechahora_termino"] = df["fechahora_finalizacion"].fillna(df["fechahora_cerrado"])
        df["duracion_min"] = (df["fechahora_termino"] - df["fechahora_creacion"]).dt.total_seconds() / 60
        df["duracion_min"] = df["duracion_min"].fillna(0)

        resumen = []
        for tecnico, grupo in df.groupby("tecnico"):
            total_min = grupo["duracion_min"].sum()
            horas, minutos = divmod(int(total_min), 60)
            resumen.append({
                "tecnico": tecnico,
                "solicitudes": grupo["ticket"].nunique(),
                "tiempo_total": f"{horas:02d}:{minutos:02d}"
            })
        return sorted(resumen, key=lambda x: x["solicitudes"], reverse=True)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Error al procesar resumen por técnico")

@app.get("/resumen_clientes")
def resumen_clientes():
    try:
        df = cargar_csv()
        df["tecnico"] = df["tecnico"].fillna("Sin Técnico").apply(normalizar_texto)
        df["cliente"] = df["cliente"].fillna("Sin Cliente").apply(normalizar_texto)
        df["monto_partner"] = pd.to_numeric(df["monto_partner"], errors="coerce").fillna(0)

        resumen = df.groupby("cliente").agg(
            total_solicitudes=("ticket", "nunique"),
            costo_total=("monto_partner", "sum")
        ).reset_index()
        resumen["costo_total"] = resumen["costo_total"].round()
        

        return sorted(resumen.to_dict(orient="records"), key=lambda x: x["total_solicitudes"], reverse=True)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Error al procesar resumen por cliente")

@app.get("/detalle_tecnicos")
def detalle_tecnicos():
    try:
        df = cargar_csv()
        df["tecnico"] = df["tecnico"].fillna("Sin Técnico").apply(normalizar_texto)
        for col in ["tecnico", "cliente", "comuna", "area_negocio"]:
            df[col] = df[col].fillna(f"Sin {col.capitalize()}").apply(normalizar_texto)
        df["monto_partner"] = pd.to_numeric(df["monto_partner"], errors="coerce").fillna(0)
        df["fechahora_termino"] = df["fechahora_finalizacion"].fillna(df["fechahora_cerrado"])
        df["duracion_min"] = (df["fechahora_termino"] - df["fechahora_creacion"]).dt.total_seconds() / 60
        df["duracion_min"] = df["duracion_min"].fillna(0)

        agrupado = df.groupby(["tecnico", "cliente"]).agg(
            comuna=("comuna", "first"),
            area_negocio=("area_negocio", "first"),
            mes_anio=("fechahora_creacion", lambda x: x.dt.strftime("%Y-%m").iloc[0]),
            total_min=("duracion_min", "sum"),
            monto_total=("monto_partner", "sum")
        ).reset_index()

        agrupado["hora_atencion"] = agrupado["total_min"].apply(lambda x: f"{int(x // 60):02d}:{int(x % 60):02d}")
        agrupado["monto_partner"] = agrupado["monto_total"].round()
        agrupado = agrupado.drop(columns=["total_min", "monto_total"])

        return agrupado.to_dict(orient="records")
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Error al procesar detalle por técnico")

@app.get("/estado_solicitud")
def estado_solicitud():
    try:
        df = cargar_csv()
        df["tecnico"] = df["tecnico"].fillna("Sin Técnico").apply(normalizar_texto)
        df["estatus"] = df["estatus"].fillna("Sin Estado").apply(normalizar_texto)
        conteo = df.groupby("estatus")["ticket_replika"].nunique().reset_index(name="total")
        conteo = conteo.rename(columns={"estatus": "estado"})
        return conteo.to_dict(orient="records")
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Error al procesar estado de solicitudes")

@app.get("/metricas_generales")
def metricas_generales():
    try:
        df = cargar_csv()
        df["tecnico"] = df["tecnico"].fillna("Sin Técnico").apply(normalizar_texto)
        df["fechahora_termino"] = df["fechahora_finalizacion"].fillna(df["fechahora_cerrado"])
        df["duracion_min"] = (df["fechahora_termino"] - df["fechahora_creacion"]).dt.total_seconds() / 60
        df["duracion_min"] = df["duracion_min"].fillna(0)
        total_min = round(df["duracion_min"].sum())
        horas, minutos = divmod(total_min, 60)

        df["monto_partner"] = pd.to_numeric(df["monto_partner"], errors="coerce").fillna(0)
        return {
            "valor_total": round(df["monto_partner"].sum()),
            "total_solicitudes": df["ticket"].nunique(),
            "horas_totales": f"{horas:02d}:{minutos:02d}"
        }
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Error al calcular métricas generales")

@app.get("/filtros_dinamicos")
def filtros_dinamicos(cliente: str = "Todos", estado: str = "Todos", tecnico: str = "Todos", fecha: str = "Todos"):
    try:
        cliente = normalizar_texto(cliente)
        estado = normalizar_texto(estado)
        tecnico = normalizar_texto(tecnico)

        df = cargar_csv()
        df["tecnico"] = df["tecnico"].fillna("Sin Técnico").apply(normalizar_texto)
        for col in ["cliente", "tecnico", "estatus"]:
            df[col] = df[col].fillna(f"Sin {col.capitalize()}").apply(normalizar_texto)

        df["fecha_utilizada"] = df["fechahora_cerrado"].fillna(df["fechahora_finalizacion"])
        df["fecha"] = pd.to_datetime(df["fecha_utilizada"], errors="coerce").dt.strftime("%Y-%m").fillna("Sin Fecha")

        # Cálculo contextual: usar una copia filtrada según el resto
        def opciones_validas(columna, filtros):
            temp = df.copy()
            for k, v in filtros.items():
                if k != columna and v != "Todos":
                    temp = temp[temp[k] == v]
            return sorted(temp[columna].dropna().unique())

        filtros_aplicados = {
            "cliente": cliente,
            "estatus": estado,
            "tecnico": tecnico,
            "fecha": fecha
        }

        return {
            "clientes": opciones_validas("cliente", filtros_aplicados),
            "estados": opciones_validas("estatus", filtros_aplicados),
            "tecnicos": opciones_validas("tecnico", filtros_aplicados),
            "fechas": opciones_validas("fecha", filtros_aplicados)
        }
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Error al generar filtros dinámicos")

@app.get("/filtrado_combinado")
def filtrado_combinado(cliente: str = "Todos", estado: str = "Todos", tecnico: str = "Todos", fecha: str = "Todos"):
    try:
        cliente = normalizar_texto(cliente)
        estado = normalizar_texto(estado)
        tecnico = normalizar_texto(tecnico)

        df = cargar_csv()
        df["tecnico"] = df["tecnico"].fillna("Sin Técnico").apply(normalizar_texto)
        for col in ["cliente", "tecnico", "estatus"]:
            df[col] = df[col].fillna(f"Sin {col.capitalize()}").apply(normalizar_texto)
        for col in ["cliente", "tecnico", "estatus"]:
            df[col] = df[col].fillna(f"Sin {col.capitalize()}").apply(normalizar_texto)
        df["fecha_utilizada"] = df["fechahora_cerrado"].fillna(df["fechahora_finalizacion"])
        df["fecha"] = pd.to_datetime(df["fecha_utilizada"], errors="coerce").dt.strftime("%Y-%m").fillna("Sin Fecha")
        df["mes_anio"] = df["fecha"]

        df["fecha_utilizada"] = df["fechahora_cerrado"].fillna(df["fechahora_finalizacion"])
        df["fecha"] = pd.to_datetime(df["fecha_utilizada"], errors="coerce").dt.strftime("%Y-%m").fillna("Sin Fecha")

        if cliente != "Todos":
            df = df[df["cliente"] == cliente].copy()
        if estado != "Todos":
            df = df[df["estatus"] == estado].copy()
        if tecnico != "Todos":
            df = df[df["tecnico"] == tecnico].copy()
        if fecha != "Todos":
            df = df[df["fecha"] == fecha].copy()

        df["ticket_replika"] = df["ticket_replika"].fillna("SIN_TICKET")
        df["fechahora_termino"] = df["fechahora_finalizacion"].fillna(df["fechahora_cerrado"])
        df["duracion_min"] = (df["fechahora_termino"] - df["fechahora_creacion"]).dt.total_seconds() / 60
        df["duracion_min"] = df["duracion_min"].fillna(0)
        df["cliente"] = df["cliente"].fillna("Sin Cliente").apply(normalizar_texto)
        df["monto_partner"] = pd.to_numeric(df["monto_partner"], errors="coerce").fillna(0)

        resumen_tecnicos = []
        for tecnico_val, grupo in df.groupby("tecnico"):
            total_min = grupo["duracion_min"].sum()
            horas, minutos = divmod(int(total_min), 60)
            resumen_tecnicos.append({
                "tecnico": tecnico_val,
                "solicitudes": grupo["ticket"].nunique(),
                "tiempo_total": f"{horas:02d}:{minutos:02d}"
            })

        resumen_clientes = df.groupby("cliente").agg(
            total_solicitudes=("ticket", "nunique"),
            costo_total=("monto_partner", "sum")
        ).reset_index()
        resumen_clientes["costo_total"] = resumen_clientes["costo_total"].round()
        

        for col in ["comuna", "area_negocio"]:
            df[col] = df[col].fillna(f"Sin {col.capitalize()}").apply(normalizar_texto)
        df["duracion_real"] = df["duracion_min"].apply(lambda x: f"{int(x // 60):02d}:{int(x % 60):02d}")

        detalle_tecnicos = df.groupby(["tecnico", "cliente"]).agg(
            comuna=("comuna", "first"),
            area_negocio=("area_negocio", "first"),
            mes_anio=("mes_anio", "first"),
            total_min=("duracion_min", "sum"),
            monto_total=("monto_partner", "sum")
        ).reset_index()
        detalle_tecnicos["hora_atencion"] = detalle_tecnicos["total_min"].apply(lambda x: f"{int(x // 60):02d}:{int(x % 60):02d}")
        detalle_tecnicos["monto_partner"] = detalle_tecnicos["monto_total"].round()
        detalle_tecnicos = detalle_tecnicos.drop(columns=["total_min", "monto_total"])

        conteo = df.groupby("estatus")["ticket"].nunique().reset_index(name="total")
        conteo = conteo.rename(columns={"estatus": "estado"})

        total_min = round(df["duracion_min"].sum())
        horas, minutos = divmod(total_min, 60)
        metricas = {
            "valor_total": round(df["monto_partner"].sum()),
            "total_solicitudes": df["ticket"].nunique(),
            "horas_totales": f"{horas:02d}:{minutos:02d}"
        }

        return {
            "resumen_tecnicos": sorted(resumen_tecnicos, key=lambda x: x["solicitudes"], reverse=True),
            "resumen_clientes": sorted(resumen_clientes.to_dict(orient="records"), key=lambda x: x["total_solicitudes"], reverse=True),
            "detalle_tecnicos": detalle_tecnicos.to_dict(orient="records"),
            "estado_solicitud": conteo.to_dict(orient="records"),
            "metricas_generales": metricas
        }

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Error al aplicar filtro combinado")


@app.get("/tickets_detalle")
def tickets_detalle(tecnico: str = "", cliente: str = "", comuna: str = "", area: str = "", fecha: str = ""):
    try:
        cliente = normalizar_texto(cliente)
        tecnico = normalizar_texto(tecnico)
        comuna = normalizar_texto(comuna)
        area = normalizar_texto(area)

        df = cargar_csv()

        if df.empty or "cliente" not in df.columns:
            return []

        df["cliente"] = df["cliente"].fillna("Sin Cliente").apply(normalizar_texto)
        df["tecnico"] = df["tecnico"].fillna("Sin Técnico").apply(normalizar_texto)
        df["comuna"] = df["comuna"].fillna("Sin Comuna").apply(normalizar_texto)
        df["area_negocio"] = df["area_negocio"].fillna("Sin Area_negocio").apply(normalizar_texto)
        df["monto_partner"] = pd.to_numeric(df["monto_partner"], errors="coerce").fillna(0)

        df["fechahora_creacion"] = pd.to_datetime(df["fechahora_creacion"], errors="coerce")
        df["fechahora_termino"] = pd.to_datetime(df["fechahora_finalizacion"].fillna(df["fechahora_cerrado"]), errors="coerce")
        df["duracion_min"] = (df["fechahora_termino"] - df["fechahora_creacion"]).dt.total_seconds() / 60
        df["duracion_min"] = df["duracion_min"].fillna(0)
        df["duracion_real"] = df["duracion_min"].apply(lambda x: f"{int(x // 60):02d}:{int(x % 60):02d}")
        df["fecha_match"] = pd.to_datetime(df["fechahora_cerrado"], errors="coerce").dt.strftime("%Y-%m")

        if cliente:
            df = df[df["cliente"] == cliente]
        if tecnico:
            df = df[df["tecnico"] == tecnico]
        if comuna:
            df = df[df["comuna"] == comuna]
        if area:
            df = df[df["area_negocio"] == area]
        if fecha:
            df = df[df["fecha_match"] == fecha]

        if df.empty:
            return []

        detalle = df[["ticket", "fechahora_creacion", "fechahora_finalizacion", "fechahora_cerrado", "duracion_real", "monto_partner"]].copy()
        detalle["fechahora_creacion"] = detalle["fechahora_creacion"].dt.strftime("%Y-%m-%d")
        detalle["fechahora_finalizacion"] = detalle["fechahora_finalizacion"].dt.strftime("%Y-%m-%d")
        detalle["fechahora_cerrado"] = detalle["fechahora_cerrado"].dt.strftime("%Y-%m-%d")
        detalle["monto_partner"] = detalle["monto_partner"].round()
        detalle = detalle.replace([float("inf"), float("-inf")], 0).fillna("")
        return detalle.to_dict(orient="records")

        cliente = normalizar_texto(cliente)
        tecnico = normalizar_texto(tecnico)
        comuna = normalizar_texto(comuna)
        area = normalizar_texto(area)

        df = cargar_csv()

        if df.empty or "cliente" not in df.columns:
            return []

        df["cliente"] = df["cliente"].fillna("Sin Cliente").apply(normalizar_texto)
        df["tecnico"] = df["tecnico"].fillna("Sin Técnico").apply(normalizar_texto)
        df["comuna"] = df["comuna"].fillna("Sin Comuna").apply(normalizar_texto)
        df["area_negocio"] = df["area_negocio"].fillna("Sin Area_negocio").apply(normalizar_texto)
        df["monto_partner"] = pd.to_numeric(df["monto_partner"], errors="coerce").fillna(0)

        # Convertir fechas y calcular duración
        df["fechahora_creacion"] = pd.to_datetime(df["fechahora_creacion"], errors="coerce")
        df["fechahora_termino"] = pd.to_datetime(
            df["fechahora_finalizacion"].fillna(df["fechahora_cerrado"]), errors="coerce"
        )
        df["duracion_min"] = (df["fechahora_termino"] - df["fechahora_creacion"]).dt.total_seconds() / 60
        df["duracion_min"] = df["duracion_min"].fillna(0)
        df["duracion_real"] = df["duracion_min"].apply(lambda x: f"{int(x // 60):02d}:{int(x % 60):02d}")
        df["fecha_match"] = pd.to_datetime(df["fechahora_cerrado"], errors="coerce").dt.strftime("%Y-%m")

        # Aplicar filtros
        filtrado = df[
            (df["cliente"] == cliente) &
            (df["tecnico"] == tecnico) &
            (True if not comuna else df["comuna"] == comuna) & (True if not area else df["area_negocio"] == area) &
            (True if not fecha else df["fecha_match"] == fecha)
        ].copy()

        if filtrado.empty:
            return []

        detalle = filtrado[["ticket", "fechahora_creacion", "fechahora_finalizacion", "fechahora_cerrado", "duracion_real", "monto_partner"]].copy()
        detalle["fechahora_creacion"] = detalle["fechahora_creacion"].dt.strftime("%Y-%m-%d")
        detalle["fechahora_termino"] = detalle["fechahora_finalizacion"].fillna(detalle["fechahora_cerrado"]).dt.strftime("%Y-%m-%d")
        detalle["monto_partner"] = detalle["monto_partner"].round()
        detalle = detalle.replace([float("inf"), float("-inf")], 0).fillna("")
        return detalle.to_dict(orient="records")

    except Exception as e:
        logger.error("Error en /tickets_detalle: %s", e)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Error al obtener tickets individuales")
