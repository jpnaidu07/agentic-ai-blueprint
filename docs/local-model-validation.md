# Local lifecycle validation evidence

Verified on the development Windows workstation:

- Separate Python 3.13 training environment installed from requirements-training.txt.
- PyTorch 2.8.0+cpu completed a real tensor operation. CUDA, XPU and MPS were
  unavailable in this environment; the implementation used CPU.
- Downloaded HuggingFaceTB/SmolLM2-135M-Instruct, revision
  `12fd25f77366fa6b3b4b768ec3050bf629380bac`.
- Executed LoRA training with the synthetic profile: initially three steps, then
  the default ten-step exercise. Exported adapter and merged safetensors weights.
- The ten-step run completed from cached weights without requiring network access.
- Reloaded a merged artifact and received a real response from the local
  OpenAI-compatible serving endpoint.
- Baseline and adapted exact-answer accuracy were both 0/3 on the tiny held-out
  fixture. This checkpoint was not approved for the tender application. Successful
  training is not proof of a useful model; more appropriate data/model selection
  and further evaluation are needed.
- Browser verification: opened the solution lifecycle panel and saved synthetic
  training/evaluation examples without a connected cloud helper.
- Automated tests cover profile separation, failed-quality rejection, stale
  approval rejection, application generation gating and fixed local gateway routing.
- Docker is unavailable on this Windows workstation. A real container-to-host-model
  integration test is included in the existing Docker CI job. The local inference
  server and CPU training were verified separately from that container boundary.

Checkpoints remain in ignored `.workbench` storage. Neither weights nor local
credentials are committed. These checks validate the engineering workflow, not
procurement accuracy or a production deployment.
