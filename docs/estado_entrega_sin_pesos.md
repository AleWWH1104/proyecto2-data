# Estado de la entrega sin pesos

El código, la presentación y el PDF del informe están preparados para una entrega
que declara los activos faltantes. **El informe de resultados ya está compilado y
verificado localmente e independientemente; la entrega humana sigue pendiente.**

| Artefacto | Estado observado |
| --- | --- |
| `app/`, `src/`, `uv.lock`, README | Demo local de cuatro páginas; 63 pruebas sintéticas aprobadas |
| `presentacion/presentacion.pdf` | Presentación de resultados actual, 20 páginas |
| `informe/informe.tex` | Fuente corregida; resultados históricos y límites sin pesos explícitos |
| `informe/referencias.bib` | 18 claves preservadas; APA renderizada y revisada, auditoría primaria acotada |
| `informe/informe.pdf` | Resultados, 31 páginas, 4242481 bytes; reemplazó el EDA solo después de verificación |
| `informe/fuentes_para_compilar.zip` | 16 entradas seguras: fuente, bibliografía y 14 PNG; bytes idénticos a fuentes locales |
| `informe/figuras/app_*.png` | Cuatro capturas auténticas de la aplicación local |
| CSV y figuras históricas | Conservados byte por byte; sin entrenamiento ni reevaluación |
| Pesos, `train.csv`, caché | Ausentes; recuperación diferida por el equipo |

## Capturas y alcance

Las capturas corresponden a `/`, `/Exploracion`, `/Prediccion` y `/Rendimiento` en
`http://127.0.0.1:8517`. Streamlit se inició con
`uv run streamlit run app/Inicio.py --server.address=127.0.0.1 --server.port=8517 --server.headless=true --browser.gatherUsageStats=false`.
Chrome headless usó un perfil nuevo y aislado, sin sesiones personales; captura
mediante CDP `Page.captureScreenshot`, sin editar DOM ni inyectar datos.
Ambos procesos se cerraron después. Son vistas del viewport, no capturas de toda
la página: 1440 × 1000, 1500, 1100 y 1400 píxeles de alto, respectivamente.
Predicción conserva el bloqueo por falta de checkpoints; no hay imagen cargada ni
predicción simulada. Exploración solo usa metadatos de partición. Rendimiento
muestra las medias registradas sobre los mismos 53 identificadores.

## Antes de entregar

1. Confirmar los límites de la revisión bibliográfica acotada antes de entregar.
2. La persona responsable confirma destino Drive, permisos y entrega de PDF,
   presentación, código y enlace del repositorio según la guía del curso.
   No hay URL Drive confirmada ni entrega remota realizada.

La inferencia con pesos reales sigue pendiente. Su ausencia no debe presentarse
como cumplimiento de extremo a extremo del objetivo de segmentar imágenes nuevas.

## Compilación autorizada y manifiesto local

El consentimiento «Sí, autorizar compilación SSH» permitió una sola compilación
en el host autorizado, exclusivamente dentro de la nueva carpeta de usuario
`~/proyecto2-informe-build-05dd1c1`. Se transfirieron el ZIP verificado y un auxiliar
de compilación, no el repositorio, datos, métricas ni checkpoints. Se mantiene esa
carpeta con herramientas y logs para reproducibilidad; no se alteraron otros proyectos.

TeX Live 2026 se instaló rootless con esquema `infraonly` y paquetes individuales,
sin colecciones completas, documentación ni fuentes. El instalador se verificó
por SHA-512; `tlmgr` confirmó el repositorio oficial
`https://ctan.math.illinois.edu/systems/texlive/tlnet` como verificado.
pdfTeX 1.40.29, Biber 2.22, biblatex 3.22a y APA 9.20 son compatibles.
La carpeta ocupa 423072 KiB según la medición posterior al build.
No hubo sudo, cambios de seguridad, GPU, entrenamiento ni evaluación nueva.

Desde los fuentes extraídos se ejecutó, con salida 0 en cada etapa:

```bash
pdflatex -no-shell-escape -interaction=nonstopmode -halt-on-error informe.tex
biber informe
pdflatex -no-shell-escape -interaction=nonstopmode -halt-on-error informe.tex
pdflatex -no-shell-escape -interaction=nonstopmode -halt-on-error informe.tex
```

Los primeros intentos detectaron `xparse.sty` y `cmex8.tfm` ausentes; se instalaron
solo `l3packages`, `hyphen-spanish`, `amsfonts` y `cm-super` para completar estilos,
silabeo español y fuentes. El primer PDF completo mostró un desborde de 36.53539 pt;
un punto de corte permitido en `src/preprocess.py` lo resolvió sin alterar el contenido.
Se reconstruyó el ZIP y se compiló nuevamente desde esos bytes exactos.
Los fallos previos del Biber Mac (`PAR.pm`, salida 2, también con caché nueva)
y la distribución oficial alternativa idéntica no ejecutada permanecen en el historial
de tareas; no se instalaron Perl/PAR externos ni Rosetta ni se reparó el sistema Mac.

| Artefacto | SHA-256 |
| --- | --- |
| PDF final, 4242481 bytes | `0e5820b1f7bfcc953af747dfd33a5094c7260a6fa5ae325ac82a8a6932746fcf` |
| ZIP final, 4342775 bytes | `377c9f9a3e6e478157742af6bcabf1aba45528e58d0d3e9bd17158af3e704838` |
| EDA anterior, respaldo temporal de 736239 bytes | `fd76a5000217d09da7129edd83c155403b9a92df695cf644483dbc4227def1f7` |

Los hashes remoto/local coinciden. Se revisaron las 31 páginas renderizadas,
las tablas densas y las referencias: 18 entradas resueltas, autores corporativos,
acrónimos, identificadores de artículo, DOI y referencias cruzadas; 12 figuras presentes.
Las cifras siguen correspondiendo a 53 imágenes comunes, 159 registros y 29 épocas.
El log final no contiene desbordes, citas indefinidas ni solicitudes de nueva pasada;
solo el aviso esperado de shell escape deshabilitado. El PDF no tiene metadatos
de título/autor ni etiquetado accesible; no se afirma una auditoría de accesibilidad.

## Revisión bibliográfica acotada

La bibliografía contiene diez artículos de revista y ocho publicaciones de
congresos, todos citados. Las referencias de arquitectura complementan las
revisiones médicas; no se presentan como 18 artículos de revista indexada.
La revisión primaria contrastó metadatos de 16 entradas; V-Net y AdamW conservan
verificación parcial por limitaciones de acceso. Se mantuvieron sus registros,
los años de publicación de nnU-Net (2021), U-Net++ (2020) y Bidanta (2025), así
como el autor corporativo HuBMAP Consortium y el sufijo II de Herr.

- [Jain, reto multiórgano](https://www.nature.com/articles/s41467-023-40291-0):
  artículo 4656, HPA hematoxilina/DAB frente a HuBMAP PAS/H&E; el Dice individual
  0.828 corresponde a MIT-B4, no MIT-B0. Se corrigieron esas afirmaciones.
- Identificadores de artículo, no páginas: Jain multiórgano 4656,
  [Jain riñón 717](https://www.nature.com/articles/s42003-023-04848-5),
  [de Bono 22](https://api.crossref.org/works/10.1186/2041-1480-4-22),
  [Bidanta 1526](https://www.nature.com/articles/s41467-024-54591-6) y
  [Tellez 101544](https://api.crossref.org/works/10.1016/j.media.2019.101544).
  Se usa `eid`; el PDF renderiza los cinco identificadores como «Artículo», no como páginas.
- [BibTeX oficial de SegFormer](https://proceedings.neurips.cc/paper_files/paper/12547-/bibtex):
  se añadieron editores y Curran Associates, Inc.; volumen y páginas no cambiaron.
- CoaT conserva las páginas 9961–9970 de la
  [versión DOI](https://api.crossref.org/works/10.1109/ICCV48922.2021.00983).
  [CVF](https://openaccess.thecvf.com/content/ICCV2021/html/Xu_Co-Scale_Conv-Attentional_Image_Transformers_ICCV_2021_paper.html)
  muestra 9981–9990; no se mezclaron versiones ni se afirmó resolver esa discrepancia.

Indexación comprobada solo mediante páginas primarias de tres revistas:
[Nature Communications](https://www.nature.com/ncomms/aims) (MEDLINE, WoS, Scopus, DOAJ),
[Communications Biology](https://www.nature.com/commsbio/journal-information)
(MEDLINE, Scopus, SCIE) e
[IEEE Access](https://ieeeaccess.ieee.org/about/bibliometrics/#indexing-information)
(Scopus, SCIE/WoS). Esto respalda las entradas de esas revistas, no una
certificación de todas las referencias. La indexación de las otras cinco
revistas no se verificó aquí; eso no implica que no estén indexadas.
