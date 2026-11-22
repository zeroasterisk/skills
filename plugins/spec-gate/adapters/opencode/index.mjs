// OpenCode / CloudCode plugin entry. tool.execute.before throws to abort a
// gated edit; the host shows the message to the model.
// Only plugin functions may be exported here: the host calls each export.

import { createSpecGate } from '../../lib/opencode-hooks.mjs';

export const SpecGatePlugin = async ({ directory, worktree, client } = {}) =>
  createSpecGate({ directory, worktree, client });

export default SpecGatePlugin;
