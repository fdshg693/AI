/**
 * issueのワークフロー状態遷移・担当者割当。stateはステータス名からteamスコープで
 * workflowStatesクエリにより解決する（状態名をハードコードせず、チーム独自カスタマイズにも追随する）。
 * assignee には "none" を指定すると担当者を外す。
 */
export async function updateIssue(client, issueId, { status, assignee }) {
  if (!status && assignee === undefined) {
    throw new Error("--status か --assignee のいずれかを指定してください。");
  }

  const issue = await client.issue(issueId);
  const input = {};

  if (status) {
    const team = await issue.team;
    const states = await client.workflowStates({
      filter: { name: { eq: status }, team: { id: { eq: team.id } } },
    });
    const state = states.nodes[0];
    if (!state) {
      throw new Error(`チーム "${team.key}" にステータス "${status}" は存在しません。`);
    }
    input.stateId = state.id;
  }

  if (assignee === "none") {
    input.assigneeId = null;
  } else if (assignee) {
    const users = await client.users({ filter: { email: { eq: assignee } } });
    const user = users.nodes[0];
    if (!user) {
      throw new Error(`メールアドレス "${assignee}" のユーザーが見つかりません。`);
    }
    input.assigneeId = user.id;
  }

  const payload = await client.updateIssue(issueId, input);
  const updated = await payload.issue;

  return { identifier: updated?.identifier ?? issueId, success: payload.success };
}
