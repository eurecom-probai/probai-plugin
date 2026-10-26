# Local development

Use [common workflows](common.md) for workstation development and offline job preparation, with these local conventions:

- Edit code, review job scripts, estimate resources, and prepare configuration.
- Run local validation under project instructions and within available local resources.
- Do not import workload frameworks solely to identify the environment.
- Do not add HPC cache redirects to local configuration.
- Prepare single-node scripts using the target site's [Helix reference](helix.md) or [Jean Zay reference](jean-zay.md). Record unresolved accounts, QoS, filesystem paths, node capacities, and effective resource defaults during offline preparation. Resolve them through [scheduler discovery](common.md#discover-before-requesting) on the cluster before submission.
