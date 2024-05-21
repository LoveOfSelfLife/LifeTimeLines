
import { authenticated_fetch} from "@/services/auth";

async function getAlbumList() 
{
  const PHOTOS_SERVICE_URL="https://photos.ltl.richkempinski.com/photos/albums";
  
  const response = await authenticated_fetch(PHOTOS_SERVICE_URL);
  if (!response) {
    return "no albums found";
  }
  const albums = await response.json();
  return (JSON.stringify(albums));
}

export default async function ProfilePage() 
{
  const albums = await getAlbumList();
  return <p> { albums } </p>;
}
