export const filterId = (id: string): boolean =>
  id.length >= 4 && id.length <= 50 && /^[a-zA-Z0-9\-_]+$/.test(id);
export const filterName = (name: string): boolean =>
  name.length > 0 && name.length <= 50 && /^[a-zA-Z0-9\-_ ]+$/.test(name);

const randomChars = "abcdefghijklmnopqrstuvwxyz0123456789";
export const getGameName = (): string => {
  let s = "";
  for (let i = 0; i < 9; ++i) {
    s += randomChars.charAt(Math.random()*36);
  }
  return s;
};
