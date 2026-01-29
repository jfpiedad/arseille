import { GoBack } from "@/components/common/GoBack";

export const ErrorComponent = () => {
  return (
    <div className="flex h-screen items-center justify-center">
      <div className="flex flex-col items-center">
        <div className="flex flex-row gap-5 items-center justify-center">
          <div>
            <h1>Internal Error.</h1>
          </div>
        </div>
        <GoBack />
      </div>
    </div>
  );
};
