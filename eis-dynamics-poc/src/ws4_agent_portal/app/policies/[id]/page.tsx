import PolicyDetailPage from "./PolicyDetailPage";

// Static export requires at least one path - actual IDs are handled client-side
export async function generateStaticParams() {
  // Return placeholder IDs - actual routing handled by 404.html fallback to index.html
  return [{ id: '_' }];
}

export default function Page() {
  return <PolicyDetailPage />;
}
