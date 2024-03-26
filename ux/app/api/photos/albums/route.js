
import { headers } from 'next/headers'
export async function GET(request, response) {
  const auth = headers().get('authorization')
  console.log(auth);
  console.log("here in /api/photos GET method ---------------------")

  var U = 'https://photos.ltl.richkempinski.com/photos/albums'
  const res = await fetch(U, {
    method: "GET",
    headers: {
      'Content-Type': 'application/json',
      'Authorization': auth,
    },
  });
  console.log("Result from fetch entities/persons:");
  console.log(res);

  const data = await res.json();

  return Response.json({ data })
}
