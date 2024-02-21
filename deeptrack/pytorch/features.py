from deeptrack.features import Feature
from deeptrack.backend import config
import torch
import numpy as np

class ToTensor(Feature):

    def __init__(self, dtype=None, device=None, add_dim_to_number=False):
        """Converts the input to a torch tensor.
        
        Parameters
        ----------
        dtype : torch.dtype, optional
            The dtype of the resulting tensor. If None, the dtype is inferred from the input.
        device : torch.device, optional
            The device of the resulting tensor. If None, the device is inferred from the input.
        add_dim_to_number : bool, optional
            If True, a dimension is added to single numbers. This is useful when the input is a
            single number, but the output should be a tensor with a single dimension.
            Default value is False.
        """
        super().__init__(dtype=dtype, device=device, add_dim_to_number=add_dim_to_number)

    def get(self, x, dtype, device, add_dim_to_number, **kwargs):
        dtype = dtype or x.dtype
        if isinstance(x, torch.Tensor):
            ...
        elif isinstance(x, np.ndarray):
            if any(stride < 0 for stride in x.strides):
                x = x.copy()
            x = torch.from_numpy(x)
        elif isinstance(x, (int, float, bool, complex)):
            if add_dim_to_number:
                x = torch.tensor([x])
            else:
                return x
        else:
            x = torch.Tensor(x)

        if dtype:
            x = x.to(dtype)
        if device:
            x = x.to(device)
        return x