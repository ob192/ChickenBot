export default function ApiErrorBanner({ error }: { error: unknown }) {
  const message = error instanceof Error ? error.message : String(error);
  return (
    <div className="banner">
      <strong>Cannot reach the API.</strong>
      <div className="muted" style={{ fontSize: 13, marginTop: 4 }}>
        {message}
      </div>
      <div className="muted" style={{ fontSize: 13, marginTop: 8 }}>
        Check that the FastAPI service is running and that <code>API_BASE_URL</code> /{" "}
        <code>API_KEY</code> in <code>admin/.env.local</code> are correct.
      </div>
    </div>
  );
}
