import { createBrowserRouter } from "react-router-dom";

import { AppLayout } from "../components/layout/AppLayout";
import { DashboardPage } from "../pages/DashboardPage";
import { UploadPage } from "../pages/UploadPage";
import { ReviewQueuePage } from "../pages/ReviewQueuePage";
import { RecordDetailPage } from "../pages/RecordDetailPage";

export const router = createBrowserRouter([
  {
    path: "/",
    element: <AppLayout />,
    children: [
      { index: true, element: <DashboardPage /> },
      { path: "upload", element: <UploadPage /> },
      { path: "review", element: <ReviewQueuePage /> },
      { path: "records/:recordId", element: <RecordDetailPage /> }
    ]
  }
]);
