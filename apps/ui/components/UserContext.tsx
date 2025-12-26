"use client";

import type { ReactNode } from "react";
import { createContext, useContext, useMemo, useState } from "react";

export type UserPreset = {
  id: string;
  label: string;
  actor: string;
  roles: string[];
  classification: string;
  note?: string;
};

export type UserContextValue = {
  active: UserPreset;
  setActiveUser: (id: string) => void;
  presets: UserPreset[];
};

const PRESETS: UserPreset[] = [
  {
    id: "jim",
    label: "jim (SUPERUSER)",
    actor: "jim",
    roles: ["SUPERUSER"],
    classification: "REFERENCE",
    note: "Dev-only superuser context",
  },
  {
    id: "test_user_1",
    label: "test_user_1 (USER)",
    actor: "test_user_1",
    roles: ["USER"],
    classification: "REFERENCE",
    note: "Standard user context",
  },
  {
    id: "test_user_2",
    label: "test_user_2 (USER)",
    actor: "test_user_2",
    roles: ["USER"],
    classification: "REFERENCE",
    note: "Standard user context",
  },
  {
    id: "user_confidential",
    label: "user (CONFIDENTIAL)",
    actor: "user_confidential",
    roles: ["USER"],
    classification: "CONFIDENTIAL",
    note: "User with CONFIDENTIAL clearance for equality-based checks",
  },
  {
    id: "user_secret",
    label: "user (SECRET)",
    actor: "user_secret",
    roles: ["USER"],
    classification: "SECRET",
    note: "User with SECRET clearance for equality-based checks",
  },
  {
    id: "contractor",
    label: "contractor (REFERENCE)",
    actor: "contractor_1",
    roles: ["CONTRACTOR"],
    classification: "REFERENCE",
    note: "External contractor context",
  },
];

const UserContext = createContext<UserContextValue | undefined>(undefined);

export function UserContextProvider({ children }: { children: ReactNode }) {
  const [activeId, setActiveId] = useState<string>(PRESETS[0]?.id ?? "jim");

  const active = useMemo(() => PRESETS.find((p) => p.id === activeId) ?? PRESETS[0], [activeId]);

  const value = useMemo(
    () => ({
      active,
      setActiveUser: setActiveId,
      presets: PRESETS,
    }),
    [active]
  );

  return <UserContext.Provider value={value}>{children}</UserContext.Provider>;
}

export function useUserContext(): UserContextValue {
  const ctx = useContext(UserContext);
  if (!ctx) throw new Error("UserContextProvider missing");
  return ctx;
}

export type UserContextPayload = {
  actor: string;
  roles: string[];
  classification: string;
};

export function toUserContextPayload(preset: UserPreset): UserContextPayload {
  return { actor: preset.actor, roles: preset.roles, classification: preset.classification };
}
