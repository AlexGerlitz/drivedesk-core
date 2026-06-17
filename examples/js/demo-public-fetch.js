async function main() {
  const baseUrl = (process.env.BASE_URL || "http://127.0.0.1:8080").replace(/\/$/, "");
  const response = await fetch(`${baseUrl}/demo/public`, {
    headers: {
      Accept: "application/json",
    },
  });

  if (!response.ok) {
    throw new Error(`GET /demo/public failed: ${response.status}`);
  }

  const payload = await response.json();

  if (payload.schemaVersion !== 1) {
    throw new Error(`unexpected schemaVersion: ${payload.schemaVersion}`);
  }

  if (payload.dataSource !== "api.synthetic") {
    throw new Error(`unexpected dataSource: ${payload.dataSource}`);
  }

  if (payload.apiContract?.path !== "/demo/public") {
    throw new Error(`unexpected apiContract.path: ${payload.apiContract?.path}`);
  }

  if (payload.tenant?.slug !== "demo-academy") {
    throw new Error(`unexpected tenant slug: ${payload.tenant?.slug}`);
  }

  console.log(
    "js demo client ok:",
    payload.tenant.slug,
    payload.dataSource,
    `workQueue=${payload.workQueue.length}`,
  );
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
