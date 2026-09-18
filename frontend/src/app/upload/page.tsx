import React from "react";
import UploadForm from "@/components/UploadForm";

export default function UploadPage({
  searchParams,
}: {
  searchParams?: { lowConfidence?: string };
}) {
  return (
    <UploadForm
      initialLowConfidence={searchParams?.lowConfidence === "true"}
    />
  );
}
