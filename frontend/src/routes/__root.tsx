import { QueryClient } from "@tanstack/react-query";
// import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
import {
  HeadContent,
  Outlet,
  createRootRouteWithContext,
} from "@tanstack/react-router";
// import { TanStackRouterDevtools } from "@tanstack/react-router-devtools";

import { ErrorComponent } from "@/components/common/ErrorComponent";
import { NotFound } from "@/components/common/NotFound";

export const Route = createRootRouteWithContext<{ queryClient: QueryClient }>()(
  {
    component: () => (
      <>
        <HeadContent />
        <Outlet />
        {/* <TanStackRouterDevtools position="bottom-right" /> */}
        {/* <ReactQueryDevtools initialIsOpen={false} /> */}
      </>
    ),
    notFoundComponent: () => <NotFound />,
    errorComponent: () => <ErrorComponent />,
  },
);
