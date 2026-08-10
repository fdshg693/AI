/**
 * issueの新規作成。teamキーで解決した`teamId`は必須、projectは名前で解決し任意。
 * ワークフロー状態名と同様に、team/projectのIDはCLIにハードコードせず都度APIから解決する。
 */
export async function createIssue(client, { title, team, project, description }) {
  if (!title) {
    throw new Error("--title を指定してください。");
  }
  if (!team) {
    throw new Error("--team を指定してください（設定ファイルにも既定値が無い場合は必須です）。");
  }

  const teams = await client.teams({ filter: { key: { eq: team } } });
  const teamNode = teams.nodes[0];
  if (!teamNode) {
    throw new Error(`チーム "${team}" が見つかりません。`);
  }

  const input = { teamId: teamNode.id, title };
  if (description) input.description = description;

  if (project) {
    const projects = await client.projects({ filter: { name: { eq: project } } });
    const projectNode = projects.nodes[0];
    if (!projectNode) {
      throw new Error(`プロジェクト "${project}" が見つかりません。`);
    }
    input.projectId = projectNode.id;
  }

  const payload = await client.createIssue(input);
  const issue = await payload.issue;

  return {
    identifier: issue?.identifier ?? null,
    url: issue?.url ?? null,
    success: payload.success,
  };
}
