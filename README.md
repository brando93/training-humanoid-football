# training-humanoid-football

Camino hacia un **minijuego de fútbol hiperrealista en Unreal Engine 5**: un jugador cuyo movimiento
sale de la física, sin animaciones reproducidas, primero aprendiendo habilidades motoras y luego a jugar con el balón.

- **Base:** ProtoMotions con Anatomical SOMA + tracker y prior GPC preentrenados, ajustados con PPO en GPU.
- **Juego:** MuJoCo embebido en Unreal para la física del jugador y el balón; políticas ONNX vía NNE.
- **Infraestructura:** AWS (us-east-1), entrenamiento diario autónomo en GPU spot, tope de $50/mes.
- **Ciclo:** entrenar → evaluar → video y reporte en un issue → revisión humana → PR → siguiente corrida.
- **Agente:** Claude (vía Amazon Bedrock con OIDC) analiza los reportes y propone cambios como PRs.

Plan completo: [docs/plan.md](docs/plan.md) · Qué ya sabe hacer: [checklist de habilidades](docs/checklist_habilidades.md) · Instrucciones del agente: [CLAUDE.md](CLAUDE.md)

## Primeros pasos (Mac)
```bash
brew install gitleaks
make hooks
make login
make check-account
```

## Seguridad
Sin claves de larga duración: SSO en local, OIDC en GitHub Actions, instance profiles en EC2.
Los datos de mocap y los modelos con licencia nunca se suben al repo (ver [docs/licensing.md](docs/licensing.md)).
