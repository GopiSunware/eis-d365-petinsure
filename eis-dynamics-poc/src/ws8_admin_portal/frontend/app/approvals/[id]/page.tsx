import ApprovalDetailPage from "./ApprovalDetailPage";

// Static export requires at least one path - actual IDs are handled client-side
export async function generateStaticParams() {
  return [{ id: '_' }];
}

export default function Page() {
  return <ApprovalDetailPage />;
}
