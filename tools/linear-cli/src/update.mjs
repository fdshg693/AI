import { resolveLabelIds } from "./labels.mjs";

/**
 * issueのワークフロー状態遷移・担当者割当・ラベル追加/削除。stateはステータス名からteamスコープで
 * workflowStatesクエリにより解決する（状態名をハードコードせず、チーム独自カスタマイズにも追随する）。
 * assignee には "none" を指定すると担当者を外す。
 * addLabels/removeLabelsは現在の`issue.labelIds`を読み取り→追加/削除を計算→全体を送り直す
 * read-modify-write方式（比較更新・楽観ロックは行わない。既存のclaimと同じベストエフォート方針）。
 */
export async function updateIssue(client, issueId, { status, assignee, addLabels, removeLabels }) {
  if (!status && assignee === undefined && !addLabels?.length && !removeLabels?.length) {
    throw new Error(
      "--status / --assignee / --add-label / --remove-label のいずれかを指定してください。",
    );
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

  if (addLabels?.length || removeLabels?.length) {
    const team = await issue.team;
    const [addIds, removeIds] = await Promise.all([
      addLabels?.length ? resolveLabelIds(client, team.id, addLabels) : [],
      removeLabels?.length ? resolveLabelIds(client, team.id, removeLabels) : [],
    ]);
    const removeSet = new Set(removeIds);
    const next = new Set(issue.labelIds.filter((id) => !removeSet.has(id)));
    for (const id of addIds) next.add(id);
    input.labelIds = [...next];
  }

  const payload = await client.updateIssue(issueId, input);
  const updated = await payload.issue;

  return { identifier: updated?.identifier ?? issueId, success: payload.success };
}
