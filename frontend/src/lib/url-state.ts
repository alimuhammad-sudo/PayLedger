"use client";

import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useCallback, useMemo } from "react";

/**
 * Page state (filters, sort, page) lives in the URL query string, so any view can be
 * bookmarked or shared and the back button works. Changing anything except `page`
 * goes back to page 1.
 */
export function useUrlState<T extends Record<string, string>>(defaults: T) {
  const params = useSearchParams();
  const router = useRouter();
  const pathname = usePathname();

  const state = useMemo(() => {
    const out = { ...defaults };
    for (const key of Object.keys(defaults) as (keyof T)[]) {
      const v = params.get(key as string);
      if (v !== null) out[key] = v as T[keyof T];
    }
    return out;
  }, [params, defaults]);

  const set = useCallback(
    (changes: Partial<T>) => {
      const next: Record<string, string> = { ...state, ...changes } as Record<string, string>;
      if (!("page" in changes) && "page" in next) next.page = "1";
      const sp = new URLSearchParams();
      for (const [k, v] of Object.entries(next)) {
        if (v && v !== defaults[k]) sp.set(k, v);
      }
      const qs = sp.toString();
      router.replace(qs ? `${pathname}?${qs}` : pathname, { scroll: false });
    },
    [state, defaults, router, pathname],
  );

  return [state, set] as const;
}
