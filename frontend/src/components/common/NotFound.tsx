import { GoBack } from "@/components/common/GoBack";
import { Separator } from "@/components/ui/separator";

export const NotFound = () => {
  return (
    <div className="flex h-screen items-center justify-center">
      <div className="flex flex-col items-center">
        <div className="flex flex-row gap-5 items-center justify-center">
          <div>
            <h1>Not Found</h1>
          </div>
          <div className="h-10">
            <Separator orientation="vertical"></Separator>
          </div>
          <div>
            <h5 className="opacity-50">Page could not be found.</h5>
          </div>
        </div>
        <GoBack />
      </div>
    </div>
  );
};
