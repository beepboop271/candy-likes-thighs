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
