# training-humanoid-football

Humanoide simulado con física que aprende habilidades motoras con estilo humano y, después,
a interactuar con un balón de fútbol. Sin animaciones reproducidas: todo el movimiento sale de la física.

- **Base:** ProtoMotions + MaskedMimic preentrenado (humanoide SMPL), entrenado con PPO en GPU.
- **Infraestructura:** AWS (us-east-1), entrenamiento diario autónomo en GPU spot, tope de $50/mes.
- **Ciclo:** entrenar → evaluar → video y reporte en un issue → revisión humana → PR → siguiente corrida.
- **Agente:** Claude (vía Amazon Bedrock con OIDC) analiza los reportes y propone cambios como PRs.

Plan completo: [docs/plan.md](docs/plan.md) · Instrucciones del agente: [CLAUDE.md](CLAUDE.md)

## Primeros pasos (Mac)
```bash
brew install gitleaks
make hooks
make login
make check-account
```

## Seguridad
Sin claves de larga duración: SSO en local, OIDC en GitHub Actions, instance profiles en EC2.
Los datos de mocap con licencia (AMASS, SMPL) nunca se suben al repo.
