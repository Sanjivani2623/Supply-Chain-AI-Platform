export default function Badge({ level }: { level: string }) {
  const cls = `badge badge-${(level || "low").toLowerCase()}`;
  return <span className={cls}>{level}</span>;
}
