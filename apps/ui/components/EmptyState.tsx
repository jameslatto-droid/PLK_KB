import Link from "next/link";

type EmptyStateProps = {
  title: string;
  description: string;
  actionLabel?: string;
  actionHref?: string;
};

export default function EmptyState({ title, description, actionLabel, actionHref }: EmptyStateProps) {
  return (
    <div className="panel flex flex-col gap-3 border-dashed">
      <p className="text-lg font-semibold text-ink-800">{title}</p>
      <p className="text-sm text-ink-600">{description}</p>
      {actionLabel && actionHref ? (
        <Link
          href={actionHref}
          className="mt-2 inline-flex w-fit items-center rounded-full border border-ink-200 bg-ink-900 px-4 py-2 text-xs font-semibold text-white"
        >
          {actionLabel}
        </Link>
      ) : null}
    </div>
  );
}
