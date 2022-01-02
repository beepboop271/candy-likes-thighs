export const filterId = (id: string): boolean => /^[\w\-]{4,50}$/.test(id);
export const filterName = (name: string): boolean => /^[\w\-]{1,50}$/.test(name);

const randomChars = "abcdefghijklmnopqrstuvwxyz0123456789";
export const getGameName = (): string => {
  let s = "";
  for (let i = 0; i < 9; ++i) {
    s += randomChars.charAt(Math.random()*36);
  }
  return s;
};

export const toNumberValues = (
  obj: Record<string, string>,
): Record<string, number> =>
  Object.fromEntries(Object.entries(obj).map(
    ([k, v]): [string, number] => [k, Number(v)],
  ));

export const sleep = async (duration: number): Promise<void> =>
  new Promise((res): void => { setTimeout(res, duration); });
