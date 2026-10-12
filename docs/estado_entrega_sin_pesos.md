# Estado de la entrega sin pesos

Al 11 de octubre de 2026, el código, la presentación y la fuente del informe están
preparados para una entrega que declara los activos faltantes. **El PDF final del
informe todavía no está compilado: no entregar el PDF EDA antiguo como resultado final.**

| Artefacto | Estado observado |
| --- | --- |
| `app/`, `src/`, `uv.lock`, README | Demo local de cuatro páginas; 63 pruebas sintéticas aprobadas |
| `presentacion/presentacion.pdf` | Presentación de resultados actual, 20 páginas |
| `informe/informe.tex` | Fuente corregida; resultados históricos y límites sin pesos explícitos |
| `informe/referencias.bib` | 18 claves preservadas; correcciones mínimas con fuentes primarias, APA renderizada pendiente |
| `informe/informe.pdf` | EDA antiguo de 13 páginas, 736239 bytes; preservado, no actualizado |
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

1. Resolver el ejecutable Biber conservando APA. Los estilos `csquotes`,
   `biblatex` 3.22a, `biblatex-apa` 9.20 y la dependencia `logreq` se instalaron
   exclusivamente en el árbol TeX del usuario, con dry-run y repositorios verificados.
   El paquete oficial Biber 2.22 universal-darwin se verificó por SHA-512 contra
   la metadata del repositorio TeX Live firmado y se extrajo a un directorio
   temporal aislado. Su variante arm64 falla al iniciar: `Can't locate PAR.pm`.
   Una única recuperación con entorno explícito mínimo y caché nueva reprodujo
   la salida 2, antes de obtener una versión o procesar bibliografía. El fallo
   persiste sin las variables Perl/PAR del proceso original y no es una caché
   antigua: se extrajeron únicamente el cargador, su biblioteca Perl y la
   variante arm64, sin completar el arranque del paquete autocontenido.
   La causa interna del paquete no quedó demostrada; el mensaje no basta para
   justificar instalar PAR externo. No se instaló Perl/PAR, Rosetta ni Biber
   en el sistema. El requisito concreto es obtener un paquete oficial Biber
   2.22 arm64 corregido y funcional, compatible con BCF 3.11, antes de compilar.
   La [documentación oficial del empaquetado](https://github.com/plk/biber/blob/v2.22/BUILDERS.README)
   indica que el ejecutable debe incluir Perl y sus módulos, sin instalar Perl.
2. Compilar el informe con pdfLaTeX, Biber y dos pasadas finales de pdfLaTeX;
   revisar cifras, citas, referencias cruzadas y todas las páginas renderizadas.
   Reemplazar el PDF publicado solamente tras verificación satisfactoria.
3. Confirmar la revisión bibliográfica y la aceptación independiente del informe.
4. La persona responsable confirma destino Drive, permisos y entrega de PDF,
   presentación, código y enlace del repositorio según la guía del curso.
   No hay URL Drive confirmada ni entrega remota realizada.

La inferencia con pesos reales sigue pendiente. Su ausencia no debe presentarse
como cumplimiento de extremo a extremo del objetivo de segmentar imágenes nuevas.

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
  Se usa `eid`; el estilo APA instalado lo admite, pero su renderizado sigue pendiente.
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
