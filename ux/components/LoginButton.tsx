import { login, logout } from "@/actions/auth";
import Button from "@mui/material/Button";

export function LoginButton() {
  return (
    <form action={login}>
      <Button variant="contained" color="primary" type="submit" fullWidth>
        Login
      </Button>
    </form>
  );
}

export function LogoutButton() {
  return (
    <form action={logout}>
      <Button variant="contained" color="primary" type="submit" fullWidth>
        Logout
      </Button>
    </form>
  );
}
