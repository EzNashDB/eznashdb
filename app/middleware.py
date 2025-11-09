from pympler import muppy
from pympler.muppy import summary
from pympler.asizeof import asizeof
from django.conf import settings


class MemoryMiddleware:
    """
    Middleware to measure memory usage before and after processing a request.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        print("MemoryMiddleware initialized!")  # Confirm middleware is loaded

    def _is_media_request(self, request):
        path = request.path
        return "media" in path or (settings.MEDIA_URL and settings.MEDIA_URL in path)

    def __call__(self, request):
        print(f"MemoryMiddleware triggered for {request.path}")  # Confirm request passes through

        # if self._is_media_request(request):
        #     print("Skipping media request")
        #     return self.get_response(request)

        # Capture initial memory state
        start_objects = muppy.get_objects()
        start_size = asizeof(start_objects)

        # Print initial memory info
        print(f"Initial objects captured: {len(start_objects)} objects")

        response = self.get_response(request)

        # Capture final memory state
        end_objects = muppy.get_objects()
        end_size = asizeof(end_objects)

        # Print final memory info
        print(f"Final objects captured: {len(end_objects)} objects")

        # Print memory differences
        self._print_memory_usage(
            request.path, start_objects, end_objects, start_size, end_size, response
        )

        # Log more detailed info for certain object types (e.g., 'list')
        self._log_detailed_object_info(start_objects, "Start")
        self._log_detailed_object_info(end_objects, "End")

        return response

    def _print_memory_usage(self, path, start_objects, end_objects, start_size, end_size, response):
        print(f"\n=== Memory Usage Report for {path} ===")

        sum_start = summary.summarize(start_objects)
        sum_end = summary.summarize(end_objects)
        diff = summary.get_diff(sum_start, sum_end)

        print(f"Top 10 memory deltas after processing {path}")
        print(f"{'Type':<60} {'# Objects':>10} {'Total Size':>10}")

        for row in sorted(diff, key=lambda i: i[2], reverse=True)[:10]:
            print(f"{row[0]:<60} {row[1]:>10} {row[2]:>10}")

        print(
            f"Processed {path}: memory delta {((end_size - start_size) / 1024.0):.1f} kB "
            f"({(start_size / 1048576.0):.1f} -> {(end_size / 1048576.0):.1f} MB), "
            f"response size: {(len(response.content) / 1024.0 if hasattr(response, 'content') else 0):.1f} kB\n"
        )

    def _log_detailed_object_info(self, objects, label):
        """
        Log details about specific objects (e.g., lists, strings) and their contents.
        """
        # Log details for list objects
        list_objects = [obj for obj in objects if isinstance(obj, list)]
        if list_objects:
            print(f"\n{label} List Objects Details:")
            for idx, obj in enumerate(list_objects[:5]):  # Log up to 5 list objects
                print(f"List {idx + 1}:")
                print(f"  Length: {len(obj)}")
                print(f"  First item: {obj[0] if obj else None}")
                print(f"  Total size: {asizeof(obj)} bytes\n")
        else:
            print(f"\nNo list objects found in {label} objects.")

        # Log details for string objects
        str_objects = [obj for obj in objects if isinstance(obj, str)]
        if str_objects:
            print(f"\n{label} String Objects Details:")
            for idx, obj in enumerate(str_objects[:10]):  # Log up to 10 strings
                print(f"String {idx + 1}:")
                print(f"  Length: {len(obj)}")
                print(f"  Total size: {asizeof(obj)} bytes")
                print(f"  Sample content: {obj[:100]}...")  # Print first 100 characters for context
        else:
            print(f"\nNo string objects found in {label} objects.")
