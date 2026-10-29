/* eslint-disable react-refresh/only-export-components */
import { lazy, Suspense } from "react";
import { createBrowserRouter, Navigate, type RouteObject } from "react-router-dom";
import { ROUTES } from "@/shared/constants/routes";
import { Spinner } from "@/shared/ui/spinner";
import { ChatPage } from "@/pages/chat/ChatPage";

const AdminPage = lazy(() =>
  import("@/pages/admin/AdminPage").then((m) => ({ default: m.AdminPage })),
);
const NotFoundPage = lazy(() =>
  import("@/pages/not-found/NotFoundPage").then((m) => ({
    default: m.NotFoundPage,
  })),
);

function LazyFallback() {
  return (
    <div className="flex min-h-dvh items-center justify-center">
      <Spinner size={24} />
    </div>
  );
}

const routes: RouteObject[] = [
  {
    path: ROUTES.HOME,
    element: <Navigate to={ROUTES.CHAT} replace />,
  },
  {
    path: ROUTES.CHAT,
    element: <ChatPage />,
  },
  {
    path: ROUTES.ADMIN,
    element: (
      <Suspense fallback={<LazyFallback />}>
        <AdminPage />
      </Suspense>
    ),
  },
  {
    path: ROUTES.NOT_FOUND,
    element: (
      <Suspense fallback={<LazyFallback />}>
        <NotFoundPage />
      </Suspense>
    ),
  },
];

export const router = createBrowserRouter(routes);
