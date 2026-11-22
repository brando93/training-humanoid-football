# data/

Esta carpeta está ignorada por git, salvo este archivo.

Los datos de movimiento viven en el bucket S3 privado del proyecto (`s3://humanoid-artifacts-611606529792/data/`)
y se descargan en la instancia de entrenamiento. Nunca se suben al repo.

| Fuente | Licencia | Notas |
|---|---|---|
| Clips de ejemplo de ProtoMotions (`*_soma*_mini.pt`) | NVIDIA / ProtoMotions | Vienen con el repo; suficientes para la Fase 2 |
| BONES-SEED (Hugging Face, acceso con registro, ~114 GB) | Licencia propia de Bones Studio | Uso comercial sin confirmar; lo acepta Brandon |
| Clips propios de futbolista (video → GVHMR) | Nuestros | Ruta segura para un juego comercial |
| AMASS / SMPL | No comercial | No se usan |
